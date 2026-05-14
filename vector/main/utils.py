from asgiref.sync import async_to_sync
from django.utils import timezone

from vector.main.consumers import NotificationConsumer
from vector.main.models import Notification, TaskQueue, Employee, TicketAssignment


def notification(employee, title, message, link=None):
    Notification.objects.create(
        recipient=employee,
        title=title,
        message=message,
        link=link,
        created_at=timezone.now()
    )

def auto_assign_from_queue():
    queue_entries = TaskQueue.objects.filter(is_activated=True).order_by('-priority', 'wait_start_time')
    for entry in queue_entries:
        available_employee = Employee.objects.filter(department=entry.department, is_busy=False, is_active=True).first()
        if available_employee:
            send_websocket_notification(
                user_id=available_employee.user.id,
                notification_type='ticket_assigned',
                data={'ticket_id': ticket.id, 'message': f'Вам назначен тикет #{ticket.id}'}
            )
            ticket = entry.ticket
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
    manager = Employee.objects.filter(department=department, is_active=True).order_by('-role__power').first()
    if manager:
        notification(
            employee=manager,
            title=f'Тикет #{ticket.id} отклонён',
            message=f'Тикет "{ticket.description[:100]}" был отклонён исполнителем. Приоритет повышен до {ticket.priority}.',
            link=f'/tickets/{ticket.id}/'
        )

def send_websocket_notification(user_id, notification_type, data):
    async_to_sync(NotificationConsumer.send_to_user)(user_id, {
        'type': notification_type,
        **data
    })