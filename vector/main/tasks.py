import logging
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.utils import timezone

from .models import TaskQueue, EscalationRule, Ticket, Employee, Department, TicketAssignment

from celery import shared_task

from .utils import notification, send_websocket_notification

GLOBAL_LIMIT = 3600

@shared_task
def monitor_deadline(ticket_id):
    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return

    if ticket.deadline is None:
        return

    if ticket.status == "in_progress" and ticket.deadline < timezone.now():
        ticket.status = "expired"
        ticket.save(update_fields=['status'])



logger = logging.getLogger(__name__)

ML_SERVICE_URL = getattr(settings, 'ML_SERVICE_URL', 'http://ml-service:8000')
ML_FEEDBACK_TIMEOUT = getattr(settings, 'ML_FEEDBACK_TIMEOUT', 5)


@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def feedback_for_ml(self, ticket_id: int):
    try:
        ticket = Ticket.objects.only('id', 'description', 'category').get(id=ticket_id)
    except Ticket.DoesNotExist:
        logger.warning("feedback_for_ml: тикет %s не найден", ticket_id)
        return

    if ticket.category is None:
        logger.info("feedback_for_ml: у тикета %s нет категории", ticket_id)
        return

    try:
        response = requests.post(
            f"{ML_SERVICE_URL}/feedback",
            json={"text": ticket.description, "true_category_id": ticket.category},
            timeout=ML_FEEDBACK_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("feedback_for_ml: ошибка для тикета %s: %s", ticket_id, exc)
        raise

    logger.info("feedback_for_ml: фидбэк по тикету %s отправлен", ticket_id)

@shared_task
def check_timeouts():
    now = timezone.now()
    expired_tickets = Ticket.objects.filter(
        deadline__lt=now,
        status='in_progress'
    )
    count = expired_tickets.count()
    if count:
        expired_tickets.update(status='expired')

        for ticket in expired_tickets:
            if ticket.assignee:
                notification(
                    ticket.assignee,
                    'Тикет просрочен',
                    f'Тикет #{ticket.id} "{ticket.description[:50]}" просрочен.'
                )
    return f'Checked timeouts: {count} tickets marked as expired'

@shared_task
def cleanup_end_of_day():
    now = timezone.now()
    threshold = now - timedelta(days=30)

    old_queue = TaskQueue.objects.filter(
        is_activated=False,
        assigned_time__lt=threshold
    )
    deleted_queue = old_queue.count()
    old_queue.delete()
    old_tickets = Ticket.objects.filter(
        status__in=['closed', 'expired', 'resolved'],
        updated_at__lt=threshold
    )

    return f'Cleanup: deleted {deleted_queue} old queue entries'

@shared_task
def remind_last_employee():
    oldest_assignment = TicketAssignment.objects.filter(
        ticket__status='in_progress',
        is_resolved=False
    ).order_by('assigned_time').first()

    if not oldest_assignment:
        return "No active employee with in_progress ticket"

    employee = oldest_assignment.assignee
    ticket = oldest_assignment.ticket
    minutes_in_work = (timezone.now() - oldest_assignment.assigned_time).total_seconds() // 60

    notification(
        employee,
        'Напоминание: долгий тикет в работе',
        f'Тикет #{ticket.id} находится у вас в работе уже {int(minutes_in_work)} минут. '
        f'Пожалуйста, завершите его или передайте коллегам.'
    )
    return f"Reminder sent to {employee.name} about ticket #{ticket.id}"


@shared_task
def remind_deadline():
    from datetime import timedelta
    now = timezone.now()
    reminder_window_start = now
    reminder_window_end = now + timedelta(minutes=60)

    tickets = Ticket.objects.filter(
        status='in_progress',
        deadline__isnull=False,
        deadline__gte=reminder_window_start,
        deadline__lte=reminder_window_end
    ).select_related('assignee')

    reminded_count = 0
    for ticket in tickets:
        assignee = ticket.assignee
        if assignee and assignee.user:
            minutes_left = int((ticket.deadline - now).total_seconds() // 60)
            send_websocket_notification(
                user_id=assignee.user.id,
                notification_type='deadline_reminder',
                data={
                    'ticket_id': ticket.id,
                    'deadline': ticket.deadline.isoformat(),
                    'minutes_left': minutes_left,
                    'message': f'Дедлайн тикета #{ticket.id} наступит через {minutes_left} минут.'
                }
            )
            reminded_count += 1
    return f'Deadline reminders sent: {reminded_count} tickets'

@shared_task
def check_escalation():
    now = timezone.now()
    # Тикеты в работе или назначенные, ещё не эскалированные
    tickets = Ticket.objects.filter(
        status__in=['assigned', 'in_progress'],
    ).select_related('category', 'assignee', 'category__department')

    escalated_count = 0
    for ticket in tickets:
        # Находим активное назначение (последнее, не закрытое)
        assignment = TicketAssignment.objects.filter(
            ticket=ticket, is_resolved=False
        ).order_by('-assigned_time').first()
        if not assignment:
            continue

        # Получаем правило эскалации для категории тикета
        rule = EscalationRule.objects.filter(category=ticket.category).first()
        if not rule:
            continue

        # Время с момента назначения
        elapsed = now - assignment.assigned_time
        if elapsed.total_seconds() / 60 > rule.time_limit:
            # Эскалация: найти менеджера отдела (сотрудник с максимальной ролью)
            department = ticket.category.department
            manager = Employee.objects.filter(
                department=department,
                is_active=True
            ).order_by('-role__power').first()

            if manager and manager != ticket.assignee:
                old_assignee = ticket.assignee
                # Меняем исполнителя
                ticket.assignee = manager
                ticket.status = 'assigned'  # или оставить in_progress
                ticket.save(update_fields=['assignee', 'status'])

                # Закрываем текущее назначение
                assignment.is_resolved = True
                assignment.resolved_time = now
                assignment.save(update_fields=['is_resolved', 'resolved_time'])

                # Создаём новое назначение
                TicketAssignment.objects.create(
                    ticket=ticket,
                    assignee=manager,
                    assigner=old_assignee,  # кто передал – предыдущий исполнитель
                    assigned_time=now,
                    is_resolved=False
                )

                # Отправляем уведомления
                # 1) Менеджеру
                if manager.user:
                    send_websocket_notification(
                        user_id=manager.user.id,
                        notification_type='escalation',
                        data={
                            'ticket_id': ticket.id,
                            'message': f'Тикет #{ticket.id} эскалирован вам так как превышен лимит времени.',
                            'assigned_by': old_assignee.name if old_assignee else 'система'
                        }
                    )
                # 2) Предыдущему исполнителю (оповещение)
                if old_assignee and old_assignee.user:
                    send_websocket_notification(
                        user_id=old_assignee.user.id,
                        notification_type='escalation_handover',
                        data={
                            'ticket_id': ticket.id,
                            'message': f'Тикет #{ticket.id} передан менеджеру {manager.name} по эскалации.'
                        }
                    )
                escalated_count += 1

    return f'Esclations processed: {escalated_count} tickets escalated'

