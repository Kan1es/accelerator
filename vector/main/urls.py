from django.urls import path
from .views import shift_start, shift_end, employee_status, accept_ticket, decline_ticket, complete_ticket
from .views_analytics import ml_accuracy, analitic_agregation, avg_time, escalation_analytics, category_counter_tickets, classificate_and_create_ticket
from .views_mobile import mobile_employees_list, mobile_tickets_list, mobile_notify_employee, mobile_predict
from .views_auth import login_view, logout_view, me_view
from .views_tickets import (
    create_ticket, list_employees, list_categories, my_tickets,
    list_notifications, profile_summary, reclassify_ticket,
)

urlpatterns = [
    path('api/auth/login/', login_view, name='auth-login'),
    path('api/auth/logout/', logout_view, name='auth-logout'),
    path('api/auth/me/', me_view, name='auth-me'),
    path('api/tickets/', create_ticket, name='ticket-create'),
    path('api/tickets/my/', my_tickets, name='ticket-my'),
    path('api/employees/', list_employees, name='employees-list'),
    path('api/categories/', list_categories, name='categories-list'),
    path('api/notifications/', list_notifications, name='notifications-list'),
    path('api/profile/summary/', profile_summary, name='profile-summary'),
    path('api/shift/start/', shift_start, name='shift_start'),
    path('api/shift/end/', shift_end, name='shift_end'),
    path('api/employee/status/', employee_status, name='employee_status'),
    path('api/tickets/<int:id>/reclassify/', reclassify_ticket, name='reclassify-ticket'),
    path('api/tickets/<int:id>/accept/', accept_ticket, name='accept-ticket'),
    path('api/tickets/<int:id>/decline/', decline_ticket, name='decline-ticket'),
    path('api/tickets/<int:id>/complete/', complete_ticket, name='complete-ticket'),
    path('api/mobile/employees/', mobile_employees_list, name='mobile-employees-list'),
    path('api/mobile/tickets/', mobile_tickets_list, name='mobile-tickets-list'),
    path('api/mobile/notify/<int:employee_id>/', mobile_notify_employee, name='mobile-notify-employee'),
    path('api/mobile/predict/', mobile_predict, name='mobile-predict'),
    
    # Analytics & AI Agent
    path('analytics/ml_accuracy/', ml_accuracy, name='ml-accuracy'),
    path('analytics/aggregation/', analitic_agregation, name='analytics-aggregation'),
    path('analytics/avg_time/', avg_time, name='analytics-avg-time'),
    path('analytics/escalations/', escalation_analytics, name='analytics-escalations'),
    path('analytics/categories/', category_counter_tickets, name='analytics-categories'),
    path('api/agent/classify/', classificate_and_create_ticket, name='agent-classify-create'),
]
