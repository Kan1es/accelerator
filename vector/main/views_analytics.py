from datetime import datetime, timedelta

from django.db import transaction
from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Ticket, Employee, Department, TicketAssignment, TaskQueue, EscalationRule, Category
from .serializers import ErrorResponseSerializer, AnaliticsResponseSerializer, AvgResponseSerializer, \
    EscalationSerializer, CategorySerializer, ClassificatorSerializator, MLAccuracySerializer
from django.db.models import Count, Q

from .services.ml_client import classify_text, fetch_ml_accuracy
from .services.queue_service import push_to_queue
from .utils import auto_assign_from_queue
from django.db import transaction

@swagger_auto_schema(
    method='get',
    operation_description="Аналитика по завершённым тикетам за сегодня и неделю, "
                          "сгруппированная по сотруднику или отделу. "
                          "Параметр запроса: group_by=employee|department",
    responses={
        200: AnaliticsResponseSerializer(many=True),
        400: ErrorResponseSerializer(),
    },
    tags=['Analytics']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analitic_agregation(request):
    group_by = request.query_params.get('group_by')
    if group_by not in ('employee', 'department'):
        return Response(
            {'error': "Параметр group_by обязателен и должен быть 'employee' или 'department'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = day_start - timedelta(days=7)

    completed_statuses = ('resolved', 'closed')

    result = []

    if group_by == 'employee':
        rows = (
            Employee.objects
            .annotate(
                completed_today=Count(
                    'assignments_received',
                    filter=Q(
                        assignments_received__is_resolved=True,
                        assignments_received__resolved_time__gte=day_start,
                        assignments_received__ticket__status__in=completed_statuses,
                    ),
                ),
                completed_week=Count(
                    'assignments_received',
                    filter=Q(
                        assignments_received__is_resolved=True,
                        assignments_received__resolved_time__gte=week_start,
                        assignments_received__ticket__status__in=completed_statuses,
                    ),
                ),
            )
            .values('id', 'name', 'completed_today', 'completed_week')
        )
        for row in rows:
            result.append({
                'group_id': row['id'],
                'group_name': row['name'],
                'completed_today': row['completed_today'],
                'completed_week': row['completed_week'],
            })

    else:
        rows = (
            Department.objects
            .annotate(
                completed_today=Count(
                    'employee__assignments_received',
                    filter=Q(
                        employee__assignments_received__is_resolved=True,
                        employee__assignments_received__resolved_time__gte=day_start,
                        employee__assignments_received__ticket__status__in=completed_statuses,
                    ),
                ),
                completed_week=Count(
                    'employee__assignments_received',
                    filter=Q(
                        employee__assignments_received__is_resolved=True,
                        employee__assignments_received__resolved_time__gte=week_start,
                        employee__assignments_received__ticket__status__in=completed_statuses,
                    ),
                ),
            )
            .values('id', 'name', 'completed_today', 'completed_week')
        )
        for row in rows:
            result.append({
                'group_id': row['id'],
                'group_name': row['name'],
                'completed_today': row['completed_today'],
                'completed_week': row['completed_week'],
            })

    serializer = AnaliticsResponseSerializer(result, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

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
    temp_dep_time = []
    result = []
    records = TicketAssignment.objects.filter(assigned_time__isnull=False).select_related('ticket__creator__department')
    for record in records:
        if record.ticket and record.ticket.creator and record.ticket.creator.department:
            departament = record.ticket.creator.department.name
            avg = (record.assigned_time - record.ticket.created_at).total_seconds()
            temp_dep_time.append({
                'department' : departament,
                'time' : avg
            })

    if not temp_dep_time:
        return Response([], status=status.HTTP_200_OK)

    temp_dep_time.sort(key = lambda n: n['department'])
    current_department = temp_dep_time[0]['department']
    current_time = []
    for data in temp_dep_time:
        if data['department'] != current_department:
            avg_seconds = sum(current_time) / len(current_time) if current_time else 0
            result.append({
                'department_name': current_department,
                'avg_response_time_seconds': avg_seconds
            })
            current_department = data['department']
            current_time = [data['time']]
        else:
            current_time.append(data['time'])
    avg_seconds = sum(current_time) / len(current_time) if current_time else 0
    result.append({
        'department_name': current_department,
        'avg_response_time_seconds': avg_seconds
    })

    serializer = AvgResponseSerializer(result, many = True)
    return Response(serializer.data, status=status.HTTP_200_OK)

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
    now = timezone.now()

    ticket_escalations = {
        'waiting_timeout': 0,
        'execution_timeout': 0
    }

    tickets = Ticket.objects.all().select_related('category')
    for ticket in tickets:
        if ticket.deadline:
            if ticket.status == 'open' and ticket.deadline < now:
                ticket_escalations['waiting_timeout'] += 1

            elif ticket.status in ['assigned', 'in_progress'] and ticket.deadline < now:
                ticket_escalations['execution_timeout'] += 1
        else:
            continue

    task_queue_escalations = {
        'waiting_timeout' : 0,
        'execution_timeout' : 0
    }

    tasks = TaskQueue.objects.all()

    for task in tasks:
        rule = EscalationRule.objects.filter(category=task.ticket.category).first()
        if not rule:
            continue
        time_limit = timedelta(minutes=rule.time_limit) # time_limit задается в минутах по справке модели
        if task.is_activated and (task.wait_start_time + time_limit) < now:
            task_queue_escalations['waiting_timeout'] += 1

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
    start_str = request.query_params.get('start_date')
    end_str = request.query_params.get('end_date')

    if not start_str or not end_str:
        return Response({'error': 'Параметры start_date и end_date обязательны'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
    except ValueError:
        return Response({'error': 'Неверный формат даты. Используйте ISO формат (YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)

    if start_time > end_time:
        return Response({'error': 'Неверный ввод данных: начальная дата больше конечной'}, status=status.HTTP_400_BAD_REQUEST)

    tickets = Ticket.objects.filter(created_at__range=[start_time, end_time]).select_related('category')

    category_counts = {}
    for ticket in tickets:
        category = ticket.category.name if ticket.category else 'Без категории'
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

DEFAULT_PRIORITY = 5


@swagger_auto_schema(
    method='post',
    operation_description="Создание тикета через чат-агента: текст обращения "
                          "классифицируется ML-сервисом, тикет создаётся и помещается в очередь.",
    responses={
        201: ClassificatorSerializator(),
        400: ErrorResponseSerializer(),
        503: ErrorResponseSerializer(),
    },
    tags=['Agent']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def classificate_and_create_ticket(request):
    text = (request.data.get('text') or '').strip()
    if not text:
        return Response(
            {'error': 'Поле text обязательно и не может быть пустым'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        employee = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response(
            {'error': 'Пользователь не привязан к сотруднику'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    category_id, confidence = classify_text(text)

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response(
            {'error': f'Категория id={category_id} не найдена в БД'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # ИИ-агент не выставляет дедлайн: мы не можем нормально его определить
    # по одному сообщению. Срок останется None («Без срока») — менеджер при
    # необходимости назначит вручную через модалку.
    now = timezone.now()
    deadline = None

    with transaction.atomic():
        new_ticket = Ticket.objects.create(
            description=text,
            category=category,
            priority=DEFAULT_PRIORITY,
            status='open',
            created_at=now,
            creator=employee,
            deadline=deadline,
        )
        push_to_queue(new_ticket, priority=new_ticket.priority)
        # После коммита пробуем сразу назначить кого-нибудь свободного из отдела
        # категории. Если все заняты — тикет останется в очереди, и подхватится
        # автоматически, как только кто-то освободится (decline/complete).
        transaction.on_commit(auto_assign_from_queue)

    # Перечитаем тикет, чтобы вернуть актуальные assignee/status.
    new_ticket.refresh_from_db()

    result = {
        'category': category.name,
        'confidence': round(confidence, 4),
        'ticket_id': new_ticket.id,
    }
    serializer = ClassificatorSerializator(result)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='get',
    operation_description="Метрики точности ML-модели (accuracy по последним N примерам). "
                          "Проксирует вызов к /stats/accuracy ML-сервиса. "
                          "Параметр запроса: last_n (по умолчанию 100, максимум 10000).",
    responses={
        200: MLAccuracySerializer(),
        503: ErrorResponseSerializer(),
    },
    tags=['Analytics']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ml_accuracy(request):
    try:
        last_n = int(request.query_params.get('last_n', 100))
    except (TypeError, ValueError):
        last_n = 100

    if last_n < 1 or last_n > 10_000:
        return Response(
            {'error': 'last_n должен быть в диапазоне [1, 10000]'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = fetch_ml_accuracy(last_n=last_n)

    if data.get('available') is False:
        return Response(
            {'error': f"ML-сервис недоступен: {data.get('error', 'unknown')}"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    serializer = MLAccuracySerializer(data)
    return Response(serializer.data, status=status.HTTP_200_OK)