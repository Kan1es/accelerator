from django.contrib import admin
from .models import (
    Department, Role, Employee, WorkShift,
    Category, EscalationRule, Ticket,
    TicketAssignment, TaskQueue, Notification,
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ('id', 'name', 'parent')
    list_filter   = ('parent',)
    search_fields = ('name',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'power')
    ordering     = ('-power',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ('id', 'name', 'role', 'department', 'is_active', 'is_busy')
    list_filter   = ('role', 'department', 'is_active', 'is_busy')
    search_fields = ('name', 'user__username')
    raw_id_fields = ('user',)


@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    list_display  = ('id', 'employee', 'start_time', 'end_time', 'total_seconds', 'is_active')
    list_filter   = ('is_active',)
    search_fields = ('employee__name',)
    ordering      = ('-start_time',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('id', 'name', 'parent', 'department')
    list_filter   = ('department',)
    search_fields = ('name', 'keywords')


@admin.register(EscalationRule)
class EscalationRuleAdmin(admin.ModelAdmin):
    list_display  = ('id', 'category', 'time_limit')
    list_filter   = ('category',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display  = ('id', 'status', 'category', 'priority', 'creator', 'assignee', 'created_at', 'deadline')
    list_filter   = ('status', 'category', 'priority')
    search_fields = ('description', 'creator__name', 'assignee__name')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(TicketAssignment)
class TicketAssignmentAdmin(admin.ModelAdmin):
    list_display  = ('id', 'ticket', 'assignee', 'assigner', 'assigned_time', 'resolved_time', 'is_resolved')
    list_filter   = ('is_resolved',)
    search_fields = ('ticket__id', 'assignee__name', 'assigner__name')
    ordering      = ('-assigned_time',)


@admin.register(TaskQueue)
class TaskQueueAdmin(admin.ModelAdmin):
    list_display  = ('id', 'ticket', 'department', 'priority', 'wait_start_time', 'assigned_time', 'is_activated')
    list_filter   = ('department', 'is_activated')
    ordering      = ('-priority', 'wait_start_time')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('id', 'recipient', 'title', 'is_read', 'created_at')
    list_filter   = ('is_read',)
    search_fields = ('recipient__name', 'title', 'message')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at',)