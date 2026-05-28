from asgiref.sync import async_to_sync
from django.db.models import Count, Q
from django.utils import timezone

from .consumers import NotificationConsumer
from .models import Notification, TaskQueue, Employee, TicketAssignment, WorkShift


def notification(employee, title, message, link=None):
    Notification.objects.create(
        recipient=employee,
        title=title,
        message=message,
        link=link
    )

def _pick_least_loaded_employee(department):
    """
    Из свободных сотрудников отдела выбирает того, у кого меньше всего
    активных назначений за всю историю (round-robin по нагрузке).
    Исключает руководителей (role.power >= 5) — они только распределяют.
    Сначала пробует тех, кто на смене; если таких нет — берёт любого свободного.
    """
    now = timezone.now()
    on_shift_ids = WorkShift.objects.filter(
        is_active=True,
        start_time__lte=now,
    ).filter(Q(end_time__isnull=True) | Q(end_time__gt=now)).values('employee_id')

    base_qs = Employee.objects.filter(
        department=department,
        is_busy=False,
        is_active=True,
    ).exclude(role__power__gte=5)

    # Предпочитаем тех, кто на смене
    qs = base_qs.filter(id__in=on_shift_ids)
    if not qs.exists():
        # Фолбэк: берём любого свободного сотрудника отдела
        qs = base_qs
    qs = qs.annotate(
        active_count=Count(
            'assigned_tickets',
            filter=Q(assigned_tickets__status__in=['assigned', 'in_progress']),
        ),
        total_count=Count('assignments_received'),
    ).order_by('active_count', 'total_count', 'id')
    return qs.first()


def _pick_any_employee(department):
    """
    Для КРИТИЧЕСКИХ задач (priority >= 10): выбирает наименее загруженного
    сотрудника отдела вне зависимости от флага is_busy.
    Логика приоритетов и исключений та же, что у _pick_least_loaded_employee.
    """
    now = timezone.now()
    on_shift_ids = WorkShift.objects.filter(
        is_active=True,
        start_time__lte=now,
    ).filter(Q(end_time__isnull=True) | Q(end_time__gt=now)).values('employee_id')

    base_qs = Employee.objects.filter(
        department=department,
        is_active=True,
    ).exclude(role__power__gte=5)

    # Предпочитаем тех, кто на смене
    qs = base_qs.filter(id__in=on_shift_ids)
    if not qs.exists():
        qs = base_qs

    qs = qs.annotate(
        active_count=Count(
            'assigned_tickets',
            filter=Q(assigned_tickets__status__in=['assigned', 'in_progress']),
        ),
        total_count=Count('assignments_received'),
    ).order_by('active_count', 'total_count', 'id')
    return qs.first()


def auto_assign_from_queue():
    """
    Пробегает по всем активным записям очереди в порядке приоритета.
    Для каждой пытается назначить наименее загруженного свободного сотрудника
    отдела очереди. Если свободных нет — оставляет запись в очереди.
    """
    queue_entries = (
        TaskQueue.objects
        .filter(is_activated=True)
        .select_related('ticket', 'department')
        .order_by('-priority', 'wait_start_time')
    )

    CRITICAL_PRIORITY = 10

    assigned_count = 0
    for entry in queue_entries:
        if not entry.department:
            continue

        is_critical = entry.priority >= CRITICAL_PRIORITY
        employee = (
            _pick_any_employee(entry.department)
            if is_critical
            else _pick_least_loaded_employee(entry.department)
        )
        if not employee:
            # все заняты — следующая запись возможно из другого отдела
            continue

        ticket = entry.ticket
        ticket.assignee = employee
        ticket.status = 'assigned'
        ticket.save(update_fields=['assignee', 'status'])

        TicketAssignment.objects.create(
            ticket=ticket,
            assignee=employee,
            assigner=None,
            assigned_time=timezone.now(),
            is_resolved=False,
        )

        entry.is_activated = False
        entry.save(update_fields=['is_activated'])

        # Для критических задач сотрудник уже мог быть занят — не перезаписываем лишний раз
        if not employee.is_busy:
            employee.is_busy = True
            employee.save(update_fields=['is_busy'])

        notification(
            employee=employee,
            title=f'Новая задача #{ticket.id}',
            message=ticket.description[:200] if ticket.description else 'Без описания',
            link=f'/employee_tasks.html',
        )
        if employee.user:
            try:
                send_websocket_notification(
                    user_id=employee.user.id,
                    notification_type='ticket_assigned',
                    data={'ticket_id': ticket.id, 'message': f'Вам назначен тикет #{ticket.id}'},
                )
            except Exception:
                pass

        assigned_count += 1

    return assigned_count

def ws_notify_dept_managers(department, event_type, data):
    """
    Отправляет WebSocket-событие всем активным руководителям отдела.
    Используется для мгновенного обновления дашборда менеджера.
    """
    if not department:
        return
    managers = Employee.objects.filter(
        department=department,
        is_active=True,
        role__power__gte=5,
    ).select_related('user')
    for mgr in managers:
        if mgr.user_id:
            try:
                send_websocket_notification(mgr.user_id, event_type, data)
            except Exception:
                pass


def notify_manager(department, ticket):
    manager = Employee.objects.filter(department=department, is_active=True).first()
    if manager:
        ticket_id = ticket.id if ticket else "N/A"
        ticket_desc = ticket.description[:100] if ticket else "без описания"
        ticket_priority = ticket.priority if ticket else "N/A"
        notification(
            employee=manager,
            title=f'Тикет #{ticket_id} отклонён' if ticket else 'Рабочая смена завершена раньше времени',
            message=f'Тикет "{ticket_desc}" был отклонён исполнителем. Приоритет повышен до {ticket_priority}.' if ticket else 'Сотрудник завершил смену, отработав менее 8 часов.',
            link=f'/tickets/{ticket_id}/' if ticket else None
        )

def send_websocket_notification(user_id, notification_type, data):
    async_to_sync(NotificationConsumer.send_to_user)(user_id, {
        'type': notification_type,
        **data
    })
