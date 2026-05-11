from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch

from .models import Employee, WorkShift, Ticket
from .serializers import MobileEmployeeSerializer, ErrorResponseSerializer

@swagger_auto_schema(
    method='get',
    operation_description="Получить список сотрудников отдела для мобильного приложения",
    responses={
        200: MobileEmployeeSerializer(many=True),
        400: ErrorResponseSerializer()
    },
    tags=['Mobile API']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_employees_list(request):
    try:
        manager = request.user.employee
        department = manager.department
    except (AttributeError, Employee.DoesNotExist):
        return Response({'error': 'Пользователь не привязан к сотруднику'},
                        status=status.HTTP_400_BAD_REQUEST)

    if not department:
        return Response({'error': 'У руководителя не указан отдел'},
                        status=status.HTTP_400_BAD_REQUEST)

    employees = Employee.objects.filter(department=department)

    # Предзагрузка активных смен и текущих задач для избежания N+1 запросов
    active_shifts = WorkShift.objects.filter(is_active=True)
    active_tickets = Ticket.objects.filter(status='in_progress')

    employees = employees.prefetch_related(
        Prefetch('workshift_set', queryset=active_shifts, to_attr='active_shift'),
        Prefetch('assigned_tickets', queryset=active_tickets, to_attr='current_tickets')
    )

    result = []
    for emp in employees:
        current_ticket = emp.current_tickets[0] if emp.current_tickets else None
        
        result.append({
            'id': emp.id,
            'name': emp.name,
            'is_on_shift': bool(emp.active_shift),
            'is_busy': emp.is_busy,
            'current_task_description': current_ticket.description if current_ticket else None,
            'current_task_priority': current_ticket.priority if current_ticket else None,
        })

    serializer = MobileEmployeeSerializer(result, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
