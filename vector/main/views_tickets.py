from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Ticket, Employee, Category, TicketAssignment, Notification


def _is_manager(employee: Employee) -> bool:
    return bool(employee.role and (employee.role.power or 0) >= 5)


def _parse_deadline(value):
    """Поддерживаем ISO-datetime ('2026-05-21T18:00:00') и пары date+time."""
    if not value:
        return None
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    return None


@swagger_auto_schema(
    method='post',
    operation_description="Менеджер создаёт тикет и назначает исполнителя.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['description'],
        properties={
            'description': openapi.Schema(type=openapi.TYPE_STRING),
            'category_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'assignee_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'priority': openapi.Schema(type=openapi.TYPE_INTEGER),
            'deadline': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        },
    ),
    tags=['Tickets'],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_ticket(request):
    try:
        author = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response({'error': 'Пользователь не привязан к сотруднику'},
                        status=status.HTTP_400_BAD_REQUEST)

    if not _is_manager(author):
        return Response({'error': 'Только руководитель может создавать тикеты вручную'},
                        status=status.HTTP_403_FORBIDDEN)

    description = (request.data.get('description') or '').strip()
    if not description:
        return Response({'error': 'description обязателен'},
                        status=status.HTTP_400_BAD_REQUEST)

    category = None
    cat_id = request.data.get('category_id')
    if cat_id:
        try:
            category = Category.objects.get(id=int(cat_id))
        except (Category.DoesNotExist, ValueError, TypeError):
            return Response({'error': 'Категория не найдена'},
                            status=status.HTTP_400_BAD_REQUEST)

    assignee = None
    assignee_id = request.data.get('assignee_id')
    if assignee_id:
        try:
            assignee = Employee.objects.get(id=int(assignee_id))
        except (Employee.DoesNotExist, ValueError, TypeError):
            return Response({'error': 'Исполнитель не найден'},
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        priority = int(request.data.get('priority', 5))
    except (TypeError, ValueError):
        priority = 5

    deadline = _parse_deadline(request.data.get('deadline'))

    with transaction.atomic():
        ticket = Ticket.objects.create(
            description=description,
            category=category,
            priority=priority,
            status='assigned' if assignee else 'open',
            creator=author,
            assignee=assignee,
            deadline=deadline,
        )
        if assignee:
            TicketAssignment.objects.create(
                ticket=ticket,
                assignee=assignee,
                assigner=author,
                assigned_time=timezone.now(),
                is_resolved=False,
            )

    return Response({
        'id': ticket.id,
        'status': ticket.status,
        'description': ticket.description,
        'assignee_id': ticket.assignee_id,
        'category_id': ticket.category_id,
        'priority': ticket.priority,
        'deadline': ticket.deadline.isoformat() if ticket.deadline else None,
    }, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='get',
    operation_description="Список сотрудников отдела текущего пользователя (для выбора исполнителя).",
    tags=['Tickets'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_employees(request):
    try:
        me = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response({'error': 'Пользователь не привязан к сотруднику'},
                        status=status.HTTP_400_BAD_REQUEST)

    qs = Employee.objects.filter(is_active=True)
    if me.department:
        qs = qs.filter(department=me.department)
    qs = qs.select_related('role', 'department').order_by('name')

    data = [
        {
            'id': e.id,
            'name': e.name,
            'role': e.role.name if e.role else None,
            'department_id': e.department_id,
            'is_busy': e.is_busy,
        }
        for e in qs
    ]
    return Response(data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_description="Список категорий тикетов (для выпадающего списка в модалке).",
    tags=['Tickets'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_categories(request):
    qs = Category.objects.select_related('department').order_by('id')
    return Response(
        [
            {
                'id': c.id,
                'name': c.name,
                'department_id': c.department_id,
                'department_name': c.department.name if c.department else None,
            }
            for c in qs
        ],
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method='get',
    operation_description="Уведомления текущего пользователя (последние N). Параметр: limit (по умолчанию 50).",
    tags=['Notifications'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_notifications(request):
    try:
        me = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response({'error': 'Пользователь не привязан к сотруднику'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        limit = max(1, min(200, int(request.query_params.get('limit', 50))))
    except (TypeError, ValueError):
        limit = 50

    qs = Notification.objects.filter(recipient=me).order_by('-created_at')[:limit]
    return Response(
        [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat() if n.created_at else None,
            }
            for n in qs
        ],
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method='get',
    operation_description="Сводка для карточки профиля менеджера: имя/роль + статистика выполненных задач отдела за 7 дней.",
    tags=['Tickets'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_summary(request):
    try:
        me = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response({'error': 'Пользователь не привязан к сотруднику'},
                        status=status.HTTP_400_BAD_REQUEST)

    week_ago = timezone.now() - timedelta(days=7)
    dept = me.department

    base = Ticket.objects.all()
    if dept:
        base = base.filter(category__department=dept)
    base = base.filter(created_at__gte=week_ago)

    total = base.count()
    done = base.filter(status__in=['resolved', 'closed']).count()

    return Response({
        'name': me.name,
        'role': me.role.name if me.role else None,
        'department': dept.name if dept else None,
        'done_week': done,
        'total_week': total,
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_description="Тикеты текущего пользователя (как assignee). Для employee_dashboard.",
    tags=['Tickets'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_tickets(request):
    try:
        me = request.user.employee
    except (AttributeError, Employee.DoesNotExist):
        return Response({'error': 'Пользователь не привязан к сотруднику'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Менеджер может запросить ?assignee=<id>, чтобы посмотреть тикеты
    # произвольного сотрудника (карточка сотрудника на manager_workers.html).
    assignee_param = request.query_params.get('assignee')
    target = me
    if assignee_param:
        if not _is_manager(me):
            return Response({'error': 'Параметр assignee доступен только руководителю'},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            target = Employee.objects.get(id=int(assignee_param))
        except (Employee.DoesNotExist, ValueError, TypeError):
            return Response({'error': 'Сотрудник не найден'},
                            status=status.HTTP_404_NOT_FOUND)

    all_statuses = ['open', 'assigned', 'in_progress', 'resolved', 'closed', 'expired']

    # Суперадмин (is_staff) видит все тикеты без фильтра по исполнителю.
    if request.user.is_staff and not assignee_param:
        tickets = list(Ticket.objects.filter(
            status__in=all_statuses,
        ).select_related('category', 'creator', 'assignee').order_by('-priority', '-created_at'))
    else:
        tickets = list(Ticket.objects.filter(
            assignee=target, status__in=all_statuses,
        ).select_related('category', 'creator', 'assignee').order_by('-priority', '-created_at'))

    from .views_mobile import _latest_assigner_map
    assigner_map = _latest_assigner_map([t.id for t in tickets])

    return Response(
        [
            {
                'id': t.id,
                'status': t.status,
                'description': t.description,
                'priority': t.priority,
                'category_name': t.category.name if t.category else None,
                'creator_name': t.creator.name if t.creator else None,
                'assigner_name': assigner_map.get(t.id),
                'assignee_id': t.assignee.id if t.assignee else None,
                'assignee_name': t.assignee.name if t.assignee else None,
                'created_at': t.created_at.isoformat() if t.created_at else None,
                'deadline': t.deadline.isoformat() if t.deadline else None,
            }
            for t in tickets
        ],
        status=status.HTTP_200_OK,
    )
