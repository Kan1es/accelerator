from django.urls import path
from vector import settings
from .views import shift_start, shift_end, employee_status, accept_ticket, decline_ticket, complete_ticket
from .views_analytics import ml_accuracy
from .views_mobile import mobile_employees_list, mobile_tickets_list, mobile_notify_employee, mobile_predict

urlpatterns = [
    path('api/shift/start/', shift_start, name='shift_start'),
    path('api/shift/end/', shift_end, name='shift_end'),
    path('api/employee/status/', employee_status, name='employee_status'),
    path('api/tickets/<int:id>/accept/', accept_ticket, name='accept-ticket'),
    path('api/tickets/<int:id>/decline/', decline_ticket, name='decline-ticket'),
    path('api/tickets/<int:id>/complete/', complete_ticket, name='complete-ticket'),
    path('api/mobile/employees/', mobile_employees_list, name='mobile-employees-list'),
    path('api/mobile/tickets/', mobile_tickets_list, name='mobile-tickets-list'),
    path('api/mobile/notify/<int:employee_id>/', mobile_notify_employee, name='mobile-notify-employee'),
    path('api/mobile/predict/', mobile_predict, name='mobile-predict'),
    path('analytics/ml_accuracy/', ml_accuracy, name='ml-accuracy'),
]
