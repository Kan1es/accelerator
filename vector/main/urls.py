from django.urls import path
from vector import settings
from .views import shift_start, shift_end, employee_status, accept_ticket, decline_ticket

urlpatterns = [
    path('api/shift/start/', shift_start, name='shift_start'),
    path('api/shift/end/', shift_end, name='shift_end'),
    path('api/employee/status/', employee_status, name='employee_status'),
    path('api/tickets/<int:id>/accept/', accept_ticket, name='accept-ticket'),
    path('api/tickets/<int:id>/decline/', decline_ticket, name='decline-ticket'),
]
