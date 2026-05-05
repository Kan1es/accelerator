from datetime import datetime, timedelta
from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Ticket, Employee, Department, TicketAssignment
from .serializers import ErrorResponseSerializer, AnaliticsResponseSerializer, AvgResponseSerializer

# @swagger_auto_schema(
#     method='get',
#     operation_description="Получить аналитику по завершённым тикетам за сегодня и неделю",
#     responses={
#         200: AnaliticsResponseSerializer(),
#         400: ErrorResponseSerializer()
#     },
#     tags=['Analytics']
# )
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def analitic_agregation(request):
#     employee_department_group = request.query_params.get('group_by')
#     if employee_department_group not in ['employee', 'department']:
#         return Response({'error': 'неверный параметр ввода для агрегации(employee or department)'},
#                         status=status.HTTP_400_BAD_REQUEST)
#
#     now = datetime.now()
#     day_time = datetime(now.year, now.month, now.day)
#     week_time = day_time - timedelta(days=7)
#
#     ticket_completed = Ticket.objects.filter(status = 'resolved') | Ticket.objects.filter(status = 'closed')
#     result = []
#
#     if employee_department_group == 'employee':
#         employeers = Employee.objects.all()
#         for employee in employeers:
#             ticket_today = ticket_completed.filter()
#             #где брать время закрытия тикета?
#
#     else:
#         departments = Department.objects.all()
#         for department in departments:
#
#
#     data = {
#         'result for:': employee_department_group,
#         'fields': result
#     }
#
#     serializer = AnaliticsResponseSerializer(data, many = True)
#     return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Получить среднюю разницу ожидания между созданием текета и его назначением",
    responses={
        200: AvgResponseSerializer(),
        400: ErrorResponseSerializer()
    },
    tags=['Analytics']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def avg_time(request):
    try:
        temp_dep_time = []
        result = []
        records = TicketAssignment.objects.filter(assigned_time__isnull=False).select_related('ticket__creator__department')
        for record in records:
            if record.ticket and record.ticket.creator and record.ticket.creator.department:
                departament = record.ticket.creator.department.name
                avg = record.assigned_time - record.ticket.created_at
                temp_dep_time.append({
                    'department' : departament,
                    'time' : avg
                })
            else:
                return Response({'error' : 'Неполные данные'}, status = status.HTTP_400_BAD_REQUEST)

        temp_dep_time.sort(key = lambda n: n['departament'])
        current_department = temp_dep_time[0]['department']
        current_time = []
        for data in temp_dep_time:
            if data['department'] != current_department:
                avg_time = sum(current_time) / len(current_time) if current_time else 0
                result.append({
                    'department': current_department,
                    'time': avg_time
                })
                current_department = data['department']
                current_time = [data['time']]
            else:
                current_time.append(data['time'])
        avg_time = sum(current_time) / len(current_time) if current_time else 0
        result.append({
            'department': current_department,
            'time': avg_time
        })

        serializer = AvgResponseSerializer(result, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except:
        return Response({'error': 'Ошибка при вычислении времени отклика'},
                        status=status.HTTP_400_BAD_REQUEST)