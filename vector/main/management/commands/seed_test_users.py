from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import Department, Role, Employee, Category, EscalationRule


class Command(BaseCommand):
    help = "Создаёт тестовых пользователей (employee/manager) и связанные Department/Role/Employee."

    # Категории должны совпадать с ML-моделью (category_names.json -> id 1..14).
    CATEGORIES = {
        1: 'Неисправность оборудования',
        2: 'Электрика / освещение',
        3: 'Брак / качество',
        4: 'Снабжение / расходники',
        5: 'Охрана труда',
        6: 'Кадры / HR',
        7: 'ИТ / ПО',
        8: 'Протечка / утечка',
        9: 'Плановое обслуживание',
        10: 'Обучение персонала',
        11: 'Производственное планирование',
        12: 'Прочее / непонятно',
        13: 'Офисная техника',
        14: 'Уборка / клининг',
    }

    def handle(self, *args, **options):
        with transaction.atomic():
            dept, _ = Department.objects.get_or_create(name='Цех №1', defaults={'parent': None})
            role_emp, _ = Role.objects.get_or_create(name='Сотрудник', defaults={'power': 1})
            role_mgr, _ = Role.objects.get_or_create(name='Руководитель отдела', defaults={'power': 5})

            # Категории + правила эскалации для всех 14 классов модели.
            for cat_id, cat_name in self.CATEGORIES.items():
                cat, _ = Category.objects.get_or_create(
                    id=cat_id,
                    defaults={'name': cat_name, 'department': dept},
                )
                # name мог быть пустым из старого seed — синхронизируем.
                if cat.name != cat_name:
                    cat.name = cat_name
                    cat.save(update_fields=['name'])
                EscalationRule.objects.get_or_create(
                    category=cat,
                    defaults={'time_limit': 30},
                )

            self._make_user(
                username='employee',
                password='1234',
                name='Иван Сотрудник',
                role=role_emp,
                department=dept,
            )
            self._make_user(
                username='worker2',
                password='1234',
                name='Сергей Рабочий',
                role=role_emp,
                department=dept,
            )
            self._make_user(
                username='manager',
                password='1234',
                name='Пётр Управляющий',
                role=role_mgr,
                department=dept,
            )

        self.stdout.write(self.style.SUCCESS('OK: seed-пользователи employee/1234 и manager/1234 готовы.'))

    def _make_user(self, *, username, password, name, role, department):
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.is_active = True
        user.save()

        employee, _ = Employee.objects.get_or_create(
            user=user,
            defaults={'name': name, 'role': role, 'department': department, 'is_active': True},
        )
        # На случай, если Employee уже был, но без полей
        employee.name = name
        employee.role = role
        employee.department = department
        employee.is_active = True
        employee.save()

        action = 'создан' if created else 'обновлён'
        self.stdout.write(f' - {username}/{password} ({name}, {role.name}) — {action}')
