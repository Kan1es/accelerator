from datetime import datetime

from ..models import TicketAssignment, Ticket, Employee

# def push_to_queue(ticket, priority):


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

    employee.is_busy = True
    employee.current_task = ticket

    assignment = TicketAssignment.objects.create(
        ticket = ticket,
        assignee = employee,
        assigner = None,
        # Кто будет правопреемником? строчка выше
        assigned_time = datetime.now(),
        # resolved_time = ?
        is_resolved = False
    )
    return assignment

def auto_assign_from_queue():
    #Добавить проверку на только что созданный ли тикет ил на освобожд сотруд
    tickets = Ticket.objects.filter(status = 'open')
    tickets.order_by('priority')

    for ticket in tickets:
        department = ticket.category.parent

        free_employee = Employee.objects.filter(is_active = True, department = department, is_bust = False)
        if free_employee.exists():
            assign_ticket_to_employee(ticket, free_employee.first())