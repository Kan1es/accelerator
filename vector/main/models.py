from django.db import models
from django.contrib.auth.models import User

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
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_busy = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class WorkShift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    total_seconds = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

class Category(models.Model):
    name = models.CharField(max_length=255)
    keywords = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return self.name

class EscalationRule(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    time_limit = models.IntegerField(help_text="Time limit in minutes")

    def __str__(self):
        return f"Rule {self.id} for Category {self.category}"

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('expired', 'Expired'),
        ('declined', 'Declined'),
    ]
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.IntegerField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(Employee, related_name='created_tickets', on_delete=models.SET_NULL, null=True, blank=True)
    assignee = models.ForeignKey(Employee, related_name='assigned_tickets', on_delete=models.SET_NULL, null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(blank=True, null=True)
    decline_not_mine = models.BooleanField(default=False)
    declined_by = models.ForeignKey(Employee, related_name='declined_tickets', on_delete=models.SET_NULL, null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    deadline_escalated_at = models.DateTimeField(null=True, blank=True)

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
        return f"Assignment {self.id} for Ticket {self.ticket}"

class TaskQueue(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.IntegerField()
    wait_start_time = models.DateTimeField()
    assigned_time = models.DateTimeField(null=True, blank=True)
    is_activated = models.BooleanField(default=True)

class Notification(models.Model):
    recipient = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True)
