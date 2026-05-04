from datetime import datetime, timedelta
from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Ticket, Employee, Department
from .serializers import ErrorResponseSerializer, AnaliticsResponseSerializer

@swagger_auto_schema(
    method='get',
    operation_description="Получить аналитику по завершённым тикетам за сегодня и неделю",
    responses={
        200: AnaliticsResponseSerializer(),
        400: ErrorResponseSerializer()
    },
    tags=['Analytics']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analitic_agregation(request):
    employee_department_group = request.query_params.get('group_by')
    if employee_department_group not in ['employee', 'department']:
        return Response({'error': 'неверный параметр ввода для агрегации(employee or department)'},
                        status=status.HTTP_400_BAD_REQUEST)

    now = datetime.now()
    day_time = datetime(now.year, now.month, now.day)
    week_time = day_time - timedelta(days=7)

    ticket_completed = Ticket.objects.filter(status = 'resolved') | Ticket.objects.filter(status = 'closed')
    result = []

    if employee_department_group == 'employee':
        employeers = Employee.objects.all()
        for employee in employeers:
            ticket_today = ticket_completed.filter()
            #где брать время закрытия тикета?

    else:
        departments = Department.objects.all()
        for department in departments:


    data = {
        'result for:': employee_department_group,
        'fields': result
    }

    serializer = AnaliticsResponseSerializer(data)
    return Response(serializer.data, status=status.HTTP_200_OK)