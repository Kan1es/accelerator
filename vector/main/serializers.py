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
    shift_time = serializers.IntegerField()

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


class AvgResponseSerializer(serializers.Serializer):
    department_name = serializers.CharField()
    avg_response_time_seconds = serializers.FloatField()

class EscalationSerializer(serializers.Serializer):
    tickets = serializers.DictField(child=serializers.IntegerField())
    task_queue = serializers.DictField(child=serializers.IntegerField())

class CategorySerializer(serializers.Serializer):
    category_name = serializers.CharField()
    ticket_count = serializers.IntegerField()

class TicketAcceptResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    detail = serializers.CharField(required=False)

class TicketDeclineResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    priority = serializers.IntegerField()
    detail = serializers.CharField(required=False)

class TicketCompleteResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    detail = serializers.CharField(required=False)

class MobileEmployeeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    is_on_shift = serializers.BooleanField()
    is_busy = serializers.BooleanField()
    current_task_description = serializers.CharField(allow_null=True, required=False)
    current_task_priority = serializers.IntegerField(allow_null=True, required=False)

class MobileTicketSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    description = serializers.CharField()
    assignee_name = serializers.CharField(allow_null=True)
    priority = serializers.IntegerField()

class SuccessResponseSerializer(serializers.Serializer):
    status = serializers.CharField()

class PredictRequestSerializer(serializers.Serializer):
    text = serializers.CharField()

class PredictResponseSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    confidence = serializers.FloatField()

class ClassificatorSerializator(serializers.Serializer):
    category = serializers.CharField()
    confidence = serializers.FloatField()
    ticket_id = serializers.IntegerField()


class AnaliticsResponseSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    group_name = serializers.CharField()
    completed_today = serializers.IntegerField()
    completed_week = serializers.IntegerField()

class MLAccuracySerializer(serializers.Serializer):
    total_samples = serializers.IntegerField()
    samples_with_prediction = serializers.IntegerField()
    correct_predictions = serializers.IntegerField()
    accuracy = serializers.FloatField()
    avg_confidence = serializers.FloatField(allow_null=True)
    last_n = serializers.IntegerField()