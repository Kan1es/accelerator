from datetime import datetime, timedelta

from django.utils import timezone

from .models import TaskQueue, EscalationRule, Ticket, Employee, Department

from celery import shared_task

GLOBAL_LIMIT = 3600
# потом подумать над глобальным максимум

def check_timeouts():
    time_now = datetime.now()
    queues_in_moment = TaskQueue.objects.filter(is_activated=True)

    for quest in queues_in_moment:
        ticket = quest.ticket
        start_quest_time = quest.assigned_time
        current_time = time_now - start_quest_time

        escalate = EscalationRule.objects.filter(category = ticket.category).first()
        if escalate.time_limit:
            time_limit = escalate.time_limit
        else:
            time_limit = GLOBAL_LIMIT

        if current_time > time_limit:
            ticket.priority += 1
        ticket.save()

        ticket_department = ticket.creator.department
        if ticket_department.parent:
            parent_department = ticket_department.parent
        else:
            parent_department = 0

        if parent_department:
            ticket.creator.department = parent_department
            ticket.save()

            #как уведомить менеджера?

        # else:

            #как уведомить админа?

    tickets_in_progress = Ticket.objects.filter(status = 'in_progress')

    for ticket in tickets_in_progress:

        deadline = ticket.deadline
        if deadline:
            if datetime.now() > deadline:
                new_ticket = Ticket(
                    description = ticket.description,
                    category = ticket.category,
                    priority = ticket.priority + 1,
                    status = 'open',
                    created_at = ticket.created_at,
                    creator = ticket.creator,
                    assignee = ticket.assignee
                )
                new_ticket.save()

                ticket_department = ticket.creator.department
                if ticket_department.parent:
                    parent_department = ticket_department.parent
                else:
                    parent_department = 0

                if parent_department:
                    ticket.creator.department = parent_department
                    ticket.save()

                #else:
                    #Вопрос остаётся, как уведомлять?

def cleanup_end_of_day():
    unfinished_tickets = Ticket.objects.filter(status = 'open', is_actual = True) | Ticket.objects.filter(status = 'assigned', is_actual = True) | Ticket.objects.filter(status = 'in_progress', is_actual = True)

    for ticket in unfinished_tickets:
        new_ticket = Ticket(
            description=ticket.description,
            category=ticket.category,
            priority=ticket.priority + 5,
            status='open',
            created_at=datetime.now() + timedelta(days=1),
            creator=ticket.creator,
            assignee=ticket.assignee
        )
        new_ticket.save()

        # archived не могу поставить статус, т.к. нету такого поля в модельке(STATUS_CHOICE)
        # ириски
        ticket.delete()

    Employee.objects.all().update(total_work_today = 0)

def remind_last_employee():
    departments = Department.objects.all()
    for department in departments:
        active_employee = department.objects.filter(is_on_shift = True, is_busy = True)
        if active_employee.count == 1:
            message = 'Ты последний активный, не забудь завершить задачи и выключить смену'

            #Аналогично, куда выводить сообщение?

@shared_task
def monitor_deadline(ticket_id):
    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return

    if ticket.status == "in_progress" and ticket.deadline < timezone.now():
        ticket.status = "expired"
        ticket.save(update_fields=['status'])