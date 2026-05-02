from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subdepartments')

    def __str__(self):
        return self.name

class Role(models.Model):
    name = models.CharField(max_length=255)
    power = models.IntegerField(help_text="Level of access/power")

    def __str__(self):
        return self.name

class Employee(models.Model):
    name = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_busy = models.BooleanField(default=False)
    # current_task = ?

    def __str__(self):
        return self.name

class WorkShift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_seconds = models.IntegerField()
    is_active = models.BooleanField(default=True)

class Category(models.Model):
    name = models.CharField(max_length=255)
    keywords = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class EscalationRule(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    time_limit = models.IntegerField(help_text="Time limit in minutes")

    def __str__(self):
        return f"Rule {self.id} for Category {self.category_id}"

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.IntegerField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField()
    creator = models.ForeignKey(Employee, related_name='created_tickets', on_delete=models.SET_NULL, null=True, blank=True)
    assignee = models.ForeignKey(Employee, related_name='assigned_tickets', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Ticket {self.id} - {self.status}"

class TicketAssignment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    assignee = models.ForeignKey(Employee, related_name='assignments_received', on_delete=models.CASCADE)
    assigner = models.ForeignKey(Employee, related_name='assignments_given', on_delete=models.CASCADE, null=True, blank=True)
    assigned_time = models.DateTimeField()
    resolved_time = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Assignment {self.id} for Ticket {self.ticket_id}"

class TaskQueue(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    # department =
    # priority =
    # wait_start_time =
    assigned_time = models.DateTimeField()
    is_activated = models.BooleanField(default=True)