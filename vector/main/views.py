from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Employee, WorkShift


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shift_start(request):
    if request.method == 'POST':
        try:
            employee = request.user.employee
        except (AttributeError, Employee.DoesNotExist):
            return Response({'error': 'Пользователь не привязан к сотруднику'},
                status=status.HTTP_400_BAD_REQUEST)

        if employee.is_on_shift:
            return Response({'error': 'Смена уже начата'},
                status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        employee.is_on_shift = True
        employee.shift_start_time = now
        employee.save()

        WorkShift.objects.create(
            employee=employee,
            start_time=now,
            is_active=True
        )

        return Response({'status': 'shift started','shift_start_time': now.isoformat()},status=status.HTTP_200_OK)