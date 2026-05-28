from django.db import transaction
from django.db.models import Q
from datetime import datetime
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


def _is_manager(employee):
    return bool(employee and employee.role and (employee.role.power or 0) >= 5)


def _employee_on_shift(employee):
    now = timezone.now()
    return WorkShift.objects.filter(
        employee=employee,
        is_active=True,
        start_time__lte=now,
    ).filter(Q(end_time__isnull=True) | Q(end_time__gt=now)).exists()


def _ticket_department(ticket):
    if ticket.category and ticket.category.department:
        return ticket.category.department
    if ticket.assignee and ticket.assignee.department:
        return ticket.assignee.department
    if ticket.creator and ticket.creator.department:
        return ticket.creator.department
    return None


def _department_manager(department):
    if not department:
        return None
    return Employee.objects.filter(
        department=department,
        is_active=True,
        role__power__gte=5,
    ).order_by('-role__power', 'id').first()


def _parse_deadline(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


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
    if ticket.status in ('resolved', 'closed', 'expired', 'declined'):
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

    if ticket.status in ('resolved', 'closed', 'expired', 'declined'):
        return Response(
            {'error': f'Нельзя отклонить тикет в статусе {ticket.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    reason = (request.data.get('reason') or '').strip()
    not_mine = bool(request.data.get('not_mine'))

    with transaction.atomic():
        ticket = Ticket.objects.select_for_update().get(id=id)
        if ticket.assignee != employee:
            return Response({'error': 'Исполнитель изменился'}, status=status.HTTP_400_BAD_REQUEST)

        employee.is_busy = False
        employee.save(update_fields=['is_busy'])

        ticket.assignee = None
        ticket.status = 'declined'
        ticket.decline_reason = reason
        ticket.decline_not_mine = not_mine
        ticket.declined_by = employee
        ticket.declined_at = timezone.now()
        ticket.save(update_fields=['assignee', 'status', 'decline_reason', 'decline_not_mine', 'declined_by', 'declined_at'])

        open_assignment = TicketAssignment.objects.filter(ticket=ticket, is_resolved=False).first()
        if open_assignment:
            open_assignment.resolved_time = timezone.now()
            open_assignment.is_resolved = True
            open_assignment.save(update_fields=['resolved_time', 'is_resolved'])

        department = _ticket_department(ticket) or employee.department
        TaskQueue.objects.filter(ticket=ticket, is_activated=True).update(is_activated=False)

    reason_text = reason or 'Причина не указана'
    if ticket.creator:
        Notification.objects.create(
            recipient=ticket.creator,
            title=f'Задача #{ticket.id} отклонена',
            message=f'{employee.name} не принял задачу. Причина: {reason_text}',
            link='/employee_tasks.html',
        )
    manager = _department_manager(department)
    if manager and manager != ticket.creator:
        Notification.objects.create(
            recipient=manager,
            title=f'Задача #{ticket.id} ждет переназначения',
            message=f'{employee.name} отклонил задачу. Причина: {reason_text}',
            link='/manager_tasks.html',
        )

    return Response(
        {
            'id': ticket.id,
            'status': ticket.status,
            'priority': ticket.priority,
            'detail': 'Задача отклонена и отправлена менеджеру'
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


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def reassign_ticket(request, id):
    try:
        manager = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response({'error': 'Пользователь не привязан к сотруднику'}, status=status.HTTP_400_BAD_REQUEST)
    if not (_is_manager(manager) or request.user.is_staff):
        return Response({'error': 'Только менеджер может переназначать задачи'}, status=status.HTTP_403_FORBIDDEN)

    assignee_id = request.data.get('assignee_id')
    if not assignee_id:
        return Response({'error': 'assignee_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        assignee = Employee.objects.get(id=int(assignee_id), is_active=True)
        ticket = Ticket.objects.select_related('category', 'creator', 'assignee').get(id=id)
    except (Employee.DoesNotExist, ValueError, TypeError):
        return Response({'error': 'Исполнитель не найден'}, status=status.HTTP_400_BAD_REQUEST)
    except Ticket.DoesNotExist:
        return Response({'error': 'Тикет не найден'}, status=status.HTTP_404_NOT_FOUND)

    if not _employee_on_shift(assignee):
        return Response({'error': 'Исполнитель не на смене'}, status=status.HTTP_400_BAD_REQUEST)
    if assignee.is_busy:
        return Response({'error': 'Исполнитель уже занят'}, status=status.HTTP_400_BAD_REQUEST)
    if ticket.status not in ('declined', 'open', 'assigned'):
        return Response({'error': 'Эту задачу сейчас нельзя переназначить'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        priority = int(request.data.get('priority', ticket.priority))
    except (TypeError, ValueError):
        priority = ticket.priority
    deadline = _parse_deadline(request.data.get('deadline')) if 'deadline' in request.data else ticket.deadline

    with transaction.atomic():
        ticket = Ticket.objects.select_for_update().get(id=id)
        if ticket.assignee:
            ticket.assignee.is_busy = False
            ticket.assignee.save(update_fields=['is_busy'])
        TicketAssignment.objects.filter(ticket=ticket, is_resolved=False).update(
            resolved_time=timezone.now(),
            is_resolved=True,
        )
        TaskQueue.objects.filter(ticket=ticket, is_activated=True).update(is_activated=False)

        ticket.assignee = assignee
        ticket.status = 'assigned'
        ticket.priority = max(1, min(10, priority))
        ticket.deadline = deadline
        ticket.decline_reason = ''
        ticket.decline_not_mine = False
        ticket.declined_by = None
        ticket.declined_at = None
        ticket.save(update_fields=[
            'assignee', 'status', 'priority', 'deadline', 'decline_reason',
            'decline_not_mine', 'declined_by', 'declined_at'
        ])
        TicketAssignment.objects.create(
            ticket=ticket,
            assignee=assignee,
            assigner=manager,
            assigned_time=timezone.now(),
            is_resolved=False,
        )
        assignee.is_busy = True
        assignee.save(update_fields=['is_busy'])

    Notification.objects.create(
        recipient=assignee,
        title=f'Новая задача #{ticket.id}',
        message=ticket.description[:200] if ticket.description else 'Без описания',
        link='/employee_tasks.html',
    )
    return Response({'id': ticket.id, 'status': ticket.status, 'assignee_id': assignee.id}, status=status.HTTP_200_OK)
