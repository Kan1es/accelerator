from datetime import datetime

from ..models import TicketAssignment, Ticket, Employee, TaskQueue


def push_to_queue(ticket, priority):
    department = ticket.creator.department
    cur_time = datetime.now()

    assig_time = TicketAssignment.objects.filter(ticket = ticket).first()
    assign_ticket = assig_time if assig_time else None
    TaskQueue_new = TaskQueue.objects.create(
        ticket = ticket,
        department = department,
        priority = priority,
        wait_start_time = cur_time,
        assigned_time = assig_time,
        is_activated = True
    )
    return TaskQueue_new

def assign_ticket_to_employee(ticket, employee):
    if not employee.is_active:
        raise ValueError(f"Сотрудник - {employee.name} не активен")
    if ticket.status == 'assigned' or ticket.status == 'Assigned':
        raise ValueError(f"Тикет {ticket.description} уже назначен")
    if ticket.status == 'closed' or ticket.status == 'resolved':
        raise ValueError(f"Тикет {ticket.description} недоступен")
    if ticket.status == 'in_progress' or ticket.status == 'In Progress':
        raise ValueError(f"Тикетом {ticket.description} занимается другой сотрудник")

    ticket.assignee = employee
    ticket.status = 'assigned'
    assigner = ticket.creator
    deadline = ticket.deadline

    employee.is_busy = True
    employee.save()

    assignment = TicketAssignment.objects.create(
        ticket = ticket,
        assignee = employee,
        assigner = assigner,
        assigned_time = datetime.now(),
        resolved_time = deadline,
        is_resolved = False
    )
    return assignment

def auto_assign_from_queue():
    tickets = Ticket.objects.filter(status = 'open')
    tickets.order_by('priority')

    for ticket in tickets:
        department = ticket.category.parent

        free_employee = Employee.objects.filter(is_active = True, department = department, is_busy = False)
        if free_employee.exists():
            assign_ticket_to_employee(ticket, free_employee.first())