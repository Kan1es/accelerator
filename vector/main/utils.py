from asgiref.sync import async_to_sync
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

def auto_assign_from_queue():
    queue_entries = TaskQueue.objects.filter(is_activated=True).order_by('-priority', 'wait_start_time')
    for entry in queue_entries:
        available_employee = Employee.objects.filter(department=entry.department, is_busy=False, is_active=True).first()
        if available_employee:
            ticket = entry.ticket
            if available_employee.user:
                send_websocket_notification(
                    user_id=available_employee.user.id,
                    notification_type='ticket_assigned',
                    data={'ticket_id': ticket.id, 'message': f'Вам назначен тикет #{ticket.id}'}
                )
            ticket.assignee = available_employee
            ticket.status = 'assigned'
            ticket.save(update_fields=['assignee', 'status'])
            TicketAssignment.objects.create(
                ticket=ticket,
                assignee=available_employee,
                assigner=None,
                assigned_time=timezone.now(),
                is_resolved=False
            )
            entry.is_activated = False
            entry.save(update_fields=['is_activated'])
            available_employee.is_busy = True
            available_employee.save(update_fields=['is_busy'])
            break

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