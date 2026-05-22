from asgiref.sync import async_to_sync
from django.db.models import Count, Q
from django.utils import timezone

from .consumers import NotificationConsumer
from .models import Notification, TaskQueue, Employee, TicketAssignment


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
    """
    qs = Employee.objects.filter(
        department=department,
        is_busy=False,
        is_active=True,
    ).exclude(role__power__gte=5)
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

    assigned_count = 0
    for entry in queue_entries:
        if not entry.department:
            continue
        employee = _pick_least_loaded_employee(entry.department)
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