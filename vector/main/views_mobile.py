from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch

from .models import Employee, WorkShift, Ticket
from .serializers import (
    MobileEmployeeSerializer, ErrorResponseSerializer, MobileTicketSerializer, 
    SuccessResponseSerializer, PredictRequestSerializer, PredictResponseSerializer
)
from .utils import notification
from .services.ml_client import classify_text

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
            'role': emp.role.name if emp.role else None,
            'is_on_shift': bool(emp.active_shift),
            'is_busy': emp.is_busy,
            'current_task_description': current_ticket.description if current_ticket else None,
            'current_task_priority': current_ticket.priority if current_ticket else None,
        })

    serializer = MobileEmployeeSerializer(result, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Получить список активных тикетов отдела для мобильного приложения",
    responses={
        200: MobileTicketSerializer(many=True),
        400: ErrorResponseSerializer()
    },
    tags=['Mobile API']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_tickets_list(request):
    try:
        employee = request.user.employee
        department = employee.department
    except (AttributeError, Employee.DoesNotExist):
        return Response({'error': 'Пользователь не привязан к сотруднику'},
                        status=status.HTTP_400_BAD_REQUEST)

    if not department:
        return Response({'error': 'У сотрудника не указан отдел'},
                        status=status.HTTP_400_BAD_REQUEST)

    active_statuses = ['open', 'assigned', 'in_progress', 'resolved']

    tickets = Ticket.objects.filter(
        category__department=department,
        status__in=active_statuses
    ).select_related('assignee', 'category').order_by('-priority', '-created_at')

    result = []
    for ticket in tickets:
        result.append({
            'id': ticket.id,
            'status': ticket.status,
            'description': ticket.description,
            'assignee_id': ticket.assignee.id if ticket.assignee else None,
            'assignee_name': ticket.assignee.name if ticket.assignee else None,
            'priority': ticket.priority,
            'category_name': ticket.category.name if ticket.category else None,
            'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
            'deadline': ticket.deadline.isoformat() if ticket.deadline else None,
        })

    serializer = MobileTicketSerializer(result, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_description="Отправить сотруднику срочное уведомление",
    responses={
        200: SuccessResponseSerializer(),
        404: ErrorResponseSerializer(),
        400: ErrorResponseSerializer()
    },
    tags=['Mobile API']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_notify_employee(request, employee_id):
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({'error': 'Сотрудник не найден'}, status=status.HTTP_404_NOT_FOUND)
    
    notification(
        employee=employee,
        title='Срочное уведомление',
        message='Критический дедлайн, свяжись с руководителем'
    )
    
    return Response({'status': 'sent'}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_description="Классифицировать текст обращения и получить предсказанную категорию",
    request_body=PredictRequestSerializer(),
    responses={
        200: PredictResponseSerializer(),
        400: ErrorResponseSerializer()
    },
    tags=['Mobile API']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_predict(request):
    serializer = PredictRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    text = serializer.validated_data['text']
    
    category_id, confidence = classify_text(text)
    
    result = {
        'category_id': category_id,
        'confidence': confidence
    }
    
    return Response(result, status=status.HTTP_200_OK)
