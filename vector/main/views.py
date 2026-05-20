from django.db import transaction
from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Employee, WorkShift, Ticket, Notification, TaskQueue, TicketAssignment
from .serializers import ShiftEndResponseSerializer, ErrorResponseSerializer, ShiftStartResponseSerializer, \
    EmployeeStatusSerializer, TicketAcceptResponseSerializer, TicketDeclineResponseSerializer, \
    TicketCompleteResponseSerializer

from .tasks import monitor_deadline, feedback_for_ml
from .utils import auto_assign_from_queue, notify_manager, send_websocket_notification


@swagger_auto_schema(
    method='post',
    operation_description="Начать рабочую смену",
    responses={
        200: ShiftStartResponseSerializer(),
        400: ErrorResponseSerializer()
    },
    tags=['Shifts']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shift_start(request):
    try:
        employee = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response({'error': 'Пользователь не привязан к сотруднику'},
                        status=status.HTTP_400_BAD_REQUEST)

    if WorkShift.objects.filter(employee=employee, is_active=True).exists():
        return Response({'error': 'Смена уже начата'},
                        status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()
    WorkShift.objects.create(
        employee=employee,
        start_time=now,
        is_active=True
    )

    return Response({'status': 'shift started', 'shift_start_time': now.isoformat()},
                    status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='post',
    operation_description="Завершить рабочую смену, вычислить отработанные секунды, при необходимости уведомить менеджера",
    responses={
        200: ShiftEndResponseSerializer(),
        400: ErrorResponseSerializer()
    },
    tags=['Shifts']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shift_end(request):
    try:
        employee = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response({'error': 'Пользователь не привязан к сотруднику'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        active_shift = WorkShift.objects.get(employee=employee, is_active=True)
    except WorkShift.DoesNotExist:
        return Response({'error': 'Активная смена не найдена'},
                        status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()
    shift_time= int((now - active_shift.start_time).total_seconds())


    if shift_time < 8 * 3600:
        notify_manager(employee.department, None)

    active_shift.end_time = now
    active_shift.total_seconds = shift_time
    active_shift.is_active = False
    active_shift.save()

    return Response({'status': 'shift ended', 'shift_end_time': now.isoformat(), 'shift_time': shift_time},
                    status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_description="Получить статус сотрудника: на смене, занят, остаток времени до 8 часов",
    responses={200: EmployeeStatusSerializer()}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_status(request):
    try:
        employee = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response(
            {'error': 'Пользователь не привязан к сотруднику'},
            status=status.HTTP_400_BAD_REQUEST
        )

    active_shift = WorkShift.objects.filter(employee=employee, is_active=True).first()
    is_on_shift = active_shift is not None

    remaining_shift_time = None
    if is_on_shift:
        now = timezone.now()
        shift_time = int((now - active_shift.start_time).total_seconds())
        eight_hours = 8 * 3600
        remaining_shift_time = max(0, eight_hours - shift_time)

    data = {
        'is_on_shift': is_on_shift,
        'is_busy': employee.is_busy,
        'remaining_shift_time': remaining_shift_time,
    }

    serializer = EmployeeStatusSerializer(data)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='patch',
    operation_description="Принять тикет в работу"
                          "Меняет статус тикета на 'in_progress', "
                          "запускает задачу monitor_deadline и "
                          "устанавливает флаг is_busy = True у исполнителя.",
    responses={
        200: TicketAcceptResponseSerializer(),
        400: ErrorResponseSerializer(),
        403: ErrorResponseSerializer(),
        404: ErrorResponseSerializer(),
    },
    tags=['Tickets']
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def accept_ticket(request, id):
    try:
        ticket = Ticket.objects.get(id=id)
    except Ticket.DoesNotExist:
        return Response(
            {'error': 'Тикет не найден'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        employee = request.user.employee
    except AttributeError:
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Пользователь не привязан к сотруднику'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Пользователь не привязан к сотруднику'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if ticket.assignee != employee:
        return Response(
            {'error': 'Вы не являетесь исполнителем этого тикета'},
            status=status.HTTP_403_FORBIDDEN
        )

    if ticket.status == 'in_progress':
        return Response(
            {'error': 'Тикет уже в работе'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if ticket.status in ('resolved', 'closed', 'expired'):
        return Response(
            {'error': f'Нельзя принять тикет в статусе {ticket.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if ticket.status not in ('assigned', 'open'):
        return Response(
            {'error': 'Тикет нельзя принять в работу из текущего статуса'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        ticket = Ticket.objects.select_for_update().get(id=id)

        if ticket.status == 'in_progress':
            return Response(
                {'error': 'Тикет уже в работе'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ticket.status = 'in_progress'
        ticket.save(update_fields=['status'])
        employee.is_busy = True
        employee.save(update_fields=['is_busy'])

    monitor_deadline.delay(ticket.id)

    return Response(
        {
            'id': ticket.id,
            'status': ticket.status,
            'detail': 'Тикет принят в работу'
        },
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method='patch',
    operation_description="Отклонить тикет (только для назначенного исполнителя). "
                          "Освобождает сотрудника, повышает приоритет тикета на 10, "
                          "возвращает тикет в очередь, вызывает автоназначение и "
                           "уведомляет менеджера отдела.",
    responses={
        200: TicketDeclineResponseSerializer(),
        400: ErrorResponseSerializer(),
        403: ErrorResponseSerializer(),
        404: ErrorResponseSerializer(),
    },
    tags=['Tickets']
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def decline_ticket(request, id):
    try:
        ticket = Ticket.objects.get(id=id)
    except Ticket.DoesNotExist:
        return Response(
            {'error': 'Тикет не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    try:
        employee = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response(
            {'error': 'Пользователь не привязан к сотруднику'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if ticket.assignee != employee:
        return Response(
            {'error': 'Вы не являетесь исполнителем этого тикета'},
            status=status.HTTP_403_FORBIDDEN
        )

    if ticket.status in ('resolved', 'closed', 'expired'):
        return Response(
            {'error': f'Нельзя отклонить тикет в статусе {ticket.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    with transaction.atomic():
        ticket = Ticket.objects.select_for_update().get(id=id)
        if ticket.assignee != employee:
            return Response({'error': 'Исполнитель изменился'}, status=status.HTTP_400_BAD_REQUEST)

        employee.is_busy = False
        employee.save(update_fields=['is_busy'])

        ticket.priority += 10
        ticket.assignee = None
        ticket.status = 'open'
        ticket.save(update_fields=['priority', 'assignee', 'status'])

        open_assignment = TicketAssignment.objects.filter(ticket=ticket, is_resolved=False).first()
        if open_assignment:
            open_assignment.resolved_time = timezone.now()
            open_assignment.is_resolved = True
            open_assignment.save(update_fields=['resolved_time', 'is_resolved'])

        department = None
        if ticket.category and ticket.category.department:
            department = ticket.category.department
        if not department and employee.department:
            department = employee.department

        TaskQueue.objects.create(
            ticket=ticket,
            department=department,
            priority=ticket.priority,
            wait_start_time=timezone.now(),
            assigned_time=timezone.now(),
            is_activated=True
        )

    auto_assign_from_queue()

    if department:
        notify_manager(department, ticket)

    return Response(
        {
            'id': ticket.id,
            'status': ticket.status,
            'priority': ticket.priority,
            'detail': 'Тикет отклонён, возвращён в очередь'
        },
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method='patch',
    operation_description="Завершить тикет как выполненный. "
                          "Переводит тикет в статус 'resolved', освобождает сотрудника, "
                          "записывает время завершения в TicketAssignment, "
                          "запускает задачу feedback_for_ml и "
                          "вызывает автоназначение из очереди.",
    responses={
        200: TicketCompleteResponseSerializer(),
        400: ErrorResponseSerializer(),
        403: ErrorResponseSerializer(),
        404: ErrorResponseSerializer(),
    },
    tags=['Tickets']
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def complete_ticket(request, id):
    try:
        ticket = Ticket.objects.get(id=id)
    except Ticket.DoesNotExist:
        return Response(
            {'error': 'Тикет не найден'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        employee = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response(
            {'error': 'Пользователь не привязан к сотруднику'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if ticket.assignee != employee:
        return Response(
            {'error': 'Вы не являетесь исполнителем этого тикета'},
            status=status.HTTP_403_FORBIDDEN
        )

    if ticket.status == 'resolved':
        return Response(
            {'error': 'Тикет уже завершён'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if ticket.status in ('closed', 'expired'):
        return Response(
            {'error': f'Нельзя завершить тикет в статусе {ticket.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if ticket.status not in ('in_progress', 'assigned'):
        return Response(
            {'error': 'Тикет может быть завершён только из статуса "в работе" или "назначен"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        ticket = Ticket.objects.select_for_update().get(id=id)
        if ticket.assignee != employee:
            return Response({'error': 'Исполнитель изменился'}, status=status.HTTP_400_BAD_REQUEST)

        ticket.status = 'resolved'
        ticket.save(update_fields=['status'])

        employee.is_busy = False
        employee.save(update_fields=['is_busy'])

        active_assignment = TicketAssignment.objects.filter(ticket=ticket, is_resolved=False).first()
        if active_assignment:
            active_assignment.resolved_time = timezone.now()
            active_assignment.is_resolved = True
            active_assignment.save(update_fields=['resolved_time', 'is_resolved'])

    transaction.on_commit(lambda: feedback_for_ml.delay(ticket.id))

    auto_assign_from_queue()

    return Response(
        {
            'id': ticket.id,
            'status': ticket.status,
            'detail': 'Тикет завершён'
        },
        status=status.HTTP_200_OK
    )