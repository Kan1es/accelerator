from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Employee


def _detect_role(employee: Employee) -> str:
    """
    Возвращает 'manager' если у сотрудника роль с power >= 5
    (head/руководитель), иначе 'employee'.
    """
    if employee.role and employee.role.power and employee.role.power >= 5:
        return 'manager'
    return 'employee'


def _user_payload(user, employee, token_key) -> dict:
    return {
        'token': token_key,
        'login': user.username,
        'role': _detect_role(employee),
        'name': employee.name,
        'employee_id': employee.id,
    }


@swagger_auto_schema(
    method='post',
    operation_description="Логин по username/password. Возвращает Token DRF и роль.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['login', 'password'],
        properties={
            'login': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING),
            'role': openapi.Schema(type=openapi.TYPE_STRING, description="employee|manager (опционально, для проверки)"),
        },
    ),
    tags=['Auth'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    login_val = (request.data.get('login') or '').strip()
    password = request.data.get('password') or ''
    requested_role = request.data.get('role')

    if not login_val or not password:
        return Response(
            {'error': 'Логин и пароль обязательны'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=login_val, password=password)
    if user is None:
        return Response(
            {'error': 'Неверный логин или пароль'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        employee = user.employee
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Пользователь не привязан к сотруднику'},
            status=status.HTTP_403_FORBIDDEN,
        )

    actual_role = _detect_role(employee)
    if requested_role and requested_role != actual_role:
        return Response(
            {'error': f'Учётная запись не имеет роли {requested_role}'},
            status=status.HTTP_403_FORBIDDEN,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response(_user_payload(user, employee, token.key), status=status.HTTP_200_OK)


@swagger_auto_schema(method='post', operation_description="Logout: удалить токен.", tags=['Auth'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    Token.objects.filter(user=request.user).delete()
    return Response({'status': 'logged out'}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='get', operation_description="Текущий пользователь.", tags=['Auth'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return Response(
            {'error': 'Пользователь не привязан к сотруднику'},
            status=status.HTTP_403_FORBIDDEN,
        )
    token, _ = Token.objects.get_or_create(user=request.user)
    return Response(_user_payload(request.user, employee, token.key), status=status.HTTP_200_OK)
