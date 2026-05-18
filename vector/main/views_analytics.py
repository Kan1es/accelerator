from datetime import datetime, timedelta
from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Ticket, Employee, Department, TicketAssignment, TaskQueue, EscalationRule
from .serializers import ErrorResponseSerializer, AnaliticsResponseSerializer, AvgResponseSerializer, EscalationSerializer, CategorySerializer

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

        temp_dep_time.sort(key = lambda n: n['department'])
        current_department = temp_dep_time[0]['department']
        current_time = []
        for data in temp_dep_time:
            if data['department'] != current_department:
                avg_time = sum(current_time) / len(current_time) if current_time else 0
                result.append({
                    'department': current_department,
                    'avg_wait_seconds': avg_time
                })
                current_department = data['department']
                current_time = [data['time']]
            else:
                current_time.append(data['time'])
        avg_time = sum(current_time) / len(current_time) if current_time else 0
        result.append({
            'department': current_department,
            'avg_wait_seconds': avg_time
        })

        serializer = AvgResponseSerializer(result, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except ErrorResponseSerializer:
        return Response({'error': 'Ошибка при вычислении времени отклика'},
                        status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    operation_description="Получить аналитику по эскалациям(TaskQueue и по тикетам)",
    responses={
        200: EscalationSerializer(),
        400: ErrorResponseSerializer()
    },
    tags=['Analytics']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def escalation_analytics(request):
    try:
        now = timezone.now()

        ticket_escalations = {
            'waiting_timeout': 0,
            'execution_timeout': 0
        }

        tickets = Ticket.objects.all().select_related('category')
        for ticket in tickets:

            if ticket.status == 'open' and ticket.deadline < now:
                ticket_escalations['waiting_timeout'] += 1

            elif ticket.status in ['assigned', 'in_progress'] and ticket.deadline > now:
                ticket_escalations['execution_timeout'] += 1

        task_queue_escalations = {
            'waiting_timeout' : 0,
            'execution_timeout' : 0
        }

        tasks = TaskQueue.objects.all()

        for task in tasks:
            rule = EscalationRule.objects.filter(category=task.ticket.category).first()
            if not rule:
                continue
            time_limit = timedelta(seconds=rule.time_limit)
            if task.is_activated and (task.wait_start_time + time_limit) > now:
                task_queue_escalations['waiting_timeout'] += 1
            elif task.is_activated and (task.wait_start_time + time_limit) < now:
                task_queue_escalations['execution_timeout'] += 1

        result = {
            'tickets' : {
                'waiting_timeout' : ticket_escalations['waiting_timeout'],
                'execution_timeout' : ticket_escalations['execution_timeout'],
            },
            'task_queue' : {
                'waiting_timeout' : task_queue_escalations['waiting_timeout'],
                'execution_timeout' : task_queue_escalations['execution_timeout'],
            }
        }

        serializer = EscalationSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except ErrorResponseSerializer:
        return Response({'error': 'ошибка вычисления аналитики по эскалациям'},
                    status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    operation_description="распределение тикетов по категириям за некоторое количество времени",
    responses={
        200: CategorySerializer(),
        400: ErrorResponseSerializer()
    },
    tags=['Analytics']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_counter_tickets(request):
    start_time = request.query_params.get('start_date')
    end_time = request.query_params.get('end_date')

    if not start_time or not end_time or start_time > end_time:
        return Response({'error': 'Неверный ввод даныых'}, status=status.HTTP_400_BAD_REQUEST)

    tickets = Ticket.objects.filter(created_at__range=[start_time, end_time])

    category_counts = {}
    for ticket in tickets:
        category = ticket.category.name
        if category in category_counts:
            category_counts[category] += 1
        else:
            category_counts[category] = 1

    categoryes_counters = category_counts.items()

    result = []
    for category, counter in categoryes_counters:
        result.append(
            {
                'category_name' : category,
                'ticket_count' : counter
            }
        )
    serializer = CategorySerializer(result, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# код ниже я не знаю куда пихать. Обозначил его на канбан доске голубым(не натурал, получается). И закинул в тестирование
# class ClassificatorSerializator(serializers.Serializer):
#     category = serializers.CharField()
#     confidence = serializers.FloatField()
#     ticket_id = serializers.IntegerField()
# # это в сериализаторы тыкнуть
#
# @swagger_auto_schema(
#     method='get',
#     operation_description="Создание тикета через чат",
#     responses={
#         200: ClassificatorSerializator(),
#         400: ErrorResponseSerializer()
#     },
#     tags=['Analytics']
# )
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def classificate_and_create_ticket(request):
#     try:
#         text = request.data.get('text')
#         category = text.get('category')
#         employee = request.user.employee
#
#         processed_text = classify_text(text) # такой функции еще нет, нужен фильтр блума
#         escalation_rule = EscalationRule.objects.filter(category_id=category).first()
#         new_ticket = Ticket.objects.create(
#             description = text,
#             category = category, #прописано в тз category_id но такого поля нет
#             priority = , #какой у нас средний по умолчанию приоритет?
#             deadline = escalation_rule.time_limit,
#             status = 'open',
#             creator = employee,
#             created_at = datetime.now()
#         )
#
#         push_to_queue(new_ticket, priority=new_ticket.priority)
#
#         result = {
#             'category': new_ticket.category.name,
#             # 'confidence': confidence,     откуда мы получаем confindece?
#             'ticket_id': new_ticket.id
#         }
#
#         serializer = ClassificatorSerializator(result)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#     except:
#         return Response({'error': 'ошибка'}, status=status.HTTP_400_BAD_REQUEST)