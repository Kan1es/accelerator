from ..models import TicketAssignment, Ticket, Employee, TaskQueue
from ..utils import auto_assign_from_queue
from django.utils import timezone


def push_to_queue(ticket, priority):
    # Сначала пытаемся взять отдел из категории тикета (то есть «куда задача
    # должна попасть по сути»). Если категории нет — fallback на отдел инициатора.
    department = None
    if ticket.category and ticket.category.department:
        department = ticket.category.department
    elif ticket.creator:
        department = ticket.creator.department
    cur_time = timezone.now()

    assig_time = TicketAssignment.objects.filter(ticket=ticket).first()
    assign_ticket = assig_time.assigned_time if assig_time else cur_time
    TaskQueue_new = TaskQueue.objects.create(
        ticket=ticket,
        department=department,
        priority=priority,
        wait_start_time=cur_time,
        assigned_time=assign_ticket,
        is_activated=True
    )
    return TaskQueue_new


def assign_ticket_to_employee(ticket, employee):
    if not employee.is_active:
        raise ValueError(f"Сотрудник - {employee.name} не активен")

    status_lower = (ticket.status or '').lower()
    if status_lower == 'assigned':
        raise ValueError(f"Тикет {ticket.description} уже назначен")
    if status_lower in ('closed', 'resolved'):
        raise ValueError(f"Тикет {ticket.description} недоступен")
    if status_lower == 'in_progress':
        raise ValueError(f"Тикетом {ticket.description} занимается другой сотрудник")

    ticket.assignee = employee
    ticket.status = 'assigned'
    ticket.save(update_fields=['assignee', 'status'])

    assigner = ticket.creator
    employee.is_busy = True
    employee.save(update_fields=['is_busy'])

    assignment = TicketAssignment.objects.create(
        ticket=ticket,
        assignee=employee,
        assigner=assigner,
        assigned_time=timezone.now(),
        resolved_time=None,
        is_resolved=False
    )
    return assignment