from rest_framework import serializers
from .models import Employee, WorkShift, Role, Department

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'power']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'parent']

class EmployeeSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'name', 'role', 'department', 'is_active', 'is_busy']

class WorkShiftSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)

    class Meta:
        model = WorkShift
        fields = ['id', 'employee', 'start_time', 'end_time', 'total_seconds', 'is_active']


class ShiftStartResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    shift_start_time = serializers.DateTimeField()

class ShiftEndResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    shift_end_time = serializers.DateTimeField()
    worked_seconds = serializers.IntegerField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

class EmployeeStatusSerializer(serializers.Serializer):
    is_on_shift = serializers.BooleanField(help_text="На смене (есть активная WorkShift)")
    is_busy = serializers.BooleanField(help_text="Занят (is_busy модели Employee)")
    remaining_shift_time = serializers.IntegerField(allow_null=True, help_text="Остаток рабочего времени до 8 часов")

class ItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    tickets_today = serializers.IntegerField()
    tickets_week = serializers.IntegerField()

class AnaliticsResponseSerializer(serializers.Serializer):
    group_by = serializers.CharField()
    data = ItemSerializer()