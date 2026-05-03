from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Employee, WorkShift
from .serializers import ShiftEndResponseSerializer, ErrorResponseSerializer, ShiftStartResponseSerializer, \
    EmployeeStatusSerializer


# TODO сервис уведомлений
def notify_manager(employee):
    print(f"Уведомление менеджеру: сотрудник {employee.name} отработал менее 8 часов")
    pass

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
        notify_manager(employee)

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