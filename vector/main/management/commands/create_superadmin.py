"""
Создаёт суперадмина: Django superuser + Employee без привязки к отделу.

Логин:    superadmin
Пароль:   admin1234
Роль UI:  Управляющий (manager)

Суперадмин видит ВСЕ тикеты всех отделов через /api/tickets/my/.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import Role, Employee


class Command(BaseCommand):
    help = 'Создаёт суперадмина с доступом ко всем тикетам.'

    def handle(self, *args, **options):
        with transaction.atomic():
            role_admin, _ = Role.objects.get_or_create(
                name='Администратор',
                defaults={'power': 10},
            )

            user, created = User.objects.get_or_create(username='superadmin')
            user.set_password('admin1234')
            user.is_active = True
            user.is_staff = True       # даёт доступ ко всем тикетам
            user.is_superuser = True   # на всякий случай
            user.save()

            employee, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'name': 'Администратор системы',
                    'role': role_admin,
                    'department': None,
                    'is_active': True,
                },
            )
            employee.name = 'Администратор системы'
            employee.role = role_admin
            employee.is_active = True
            employee.save()

        action = 'создан' if created else 'обновлён'
        self.stdout.write(self.style.SUCCESS(
            f'\nsuperadmin {action}.\n'
            f'  Логин:   superadmin\n'
            f'  Пароль:  admin1234\n'
            f'  Вход:    выбрать "Я управляющий" на login.html\n'
            f'  Видит:   все тикеты всех отделов\n'
        ))
