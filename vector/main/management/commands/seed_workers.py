"""
Создаёт тестовых сотрудников (по 2 на каждый отдел, у которого есть категории)
и одного руководителя на каждый такой отдел.

Все сотрудники: пароль 1234.
Логины: dept<id>_worker1 / dept<id>_worker2 / dept<id>_manager

Запуск:
    py -3 manage.py seed_workers
    py -3 manage.py seed_workers --clear   # сначала удалить старых тест-юзеров
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import Department, Role, Employee, Category


PASSWORD = '1234'


# Человекочитаемые имена для отделов (по id из БД)
DEPT_DISPLAY = {
    2:  ('Производственный',          'prod'),
    12: ('Инструментальный цех',      'instrum'),
    13: ('Ремонтно-механический цех', 'repair'),
    14: ('Энергоцех',                 'energy'),
    15: ('ОТК',                       'otk'),
    17: ('Отдел закупок',             'zakup'),
    21: ('Бухгалтерия',               'buh'),
    22: ('Отдел кадров',              'hr'),
    24: ('Цех №1',                    'ceh1'),
}

WORKER_NAMES = [
    ('Алексей Петров',   'Анна Смирнова'),
    ('Иван Козлов',      'Мария Новикова'),
    ('Сергей Морозов',   'Ольга Соколова'),
    ('Дмитрий Волков',   'Екатерина Лебедева'),
    ('Андрей Попов',     'Татьяна Васильева'),
    ('Михаил Соловьёв',  'Наталья Зайцева'),
    ('Роман Федотов',    'Юлия Орлова'),
    ('Павел Кузнецов',   'Светлана Гусева'),
    ('Артём Никитин',    'Валерия Фомина'),
]

MANAGER_NAMES = [
    'Борис Громов',
    'Владимир Чернов',
    'Геннадий Белов',
    'Константин Рыбаков',
    'Леонид Сидоров',
    'Максим Щербаков',
    'Николай Тихонов',
    'Олег Мельников',
    'Пётр Фролов',
]


class Command(BaseCommand):
    help = 'Создаёт тестовых сотрудников по одному на каждый отдел с категориями.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить ранее созданных seed-workers перед созданием новых.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_workers()

        role_emp, _ = Role.objects.get_or_create(name='Сотрудник', defaults={'power': 1})
        role_mgr, _ = Role.objects.get_or_create(name='Руководитель отдела', defaults={'power': 5})

        # Отделы, у которых есть хотя бы одна категория
        dept_ids_with_cats = list(
            Category.objects.values_list('department_id', flat=True).distinct()
        )
        dept_ids_with_cats = [d for d in dept_ids_with_cats if d]

        depts = Department.objects.filter(id__in=dept_ids_with_cats).order_by('id')

        created_total = 0
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\nСоздаём сотрудников для {depts.count()} отделов (пароль: {PASSWORD})\n'
        ))

        for i, dept in enumerate(depts):
            slug = DEPT_DISPLAY.get(dept.id, (dept.name, f'dept{dept.id}'))[1]
            cats = list(Category.objects.filter(department=dept).values_list('id', 'name'))
            w_name1, w_name2 = WORKER_NAMES[i % len(WORKER_NAMES)]
            mgr_name = MANAGER_NAMES[i % len(MANAGER_NAMES)]

            self.stdout.write(f'\n[{dept.id}] {dept.name}')
            self.stdout.write(f'    Категории: {cats}')

            # 2 сотрудника + 1 руководитель на отдел
            specs = [
                (f'{slug}_worker1', w_name1, role_emp),
                (f'{slug}_worker2', w_name2, role_emp),
                (f'{slug}_manager', mgr_name,  role_mgr),
            ]

            for username, name, role in specs:
                emp, new = self._make_user(username, name, role, dept)
                status = 'создан' if new else 'обновлён'
                marker = '+' if new else '~'
                self.stdout.write(
                    f'    [{marker}] {username}/{PASSWORD}  ({name}, {role.name}) - {status}'
                )
                if new:
                    created_total += 1

        self.stdout.write('\n' + self.style.SUCCESS(
            f'Готово. Создано новых пользователей: {created_total}'
        ))
        self._print_summary(depts)

    def _make_user(self, username, name, role, department):
        user, created = User.objects.get_or_create(username=username)
        user.set_password(PASSWORD)
        user.is_active = True
        user.save()

        employee, emp_created = Employee.objects.get_or_create(
            user=user,
            defaults={'name': name, 'role': role, 'department': department, 'is_active': True},
        )
        employee.name = name
        employee.role = role
        employee.department = department
        employee.is_active = True
        employee.is_busy = False
        employee.save()
        return employee, created

    def _clear_workers(self):
        """Удаляет пользователей, созданных этой командой (по паттерну логина)."""
        slugs = [v[1] for v in DEPT_DISPLAY.values()]
        suffixes = ['_worker1', '_worker2', '_manager']
        usernames = [s + sfx for s in slugs for sfx in suffixes]
        deleted, _ = User.objects.filter(username__in=usernames).delete()
        self.stdout.write(f'Удалено старых пользователей: {deleted}')

    def _print_summary(self, depts):
        self.stdout.write('\n' + '-' * 70)
        self.stdout.write(self.style.MIGRATE_HEADING('ИТОГ -логины и пароли:'))
        self.stdout.write('-' * 70)
        self.stdout.write(f'{"Логин":<30} {"Роль":<20} {"Отдел"}')
        self.stdout.write('-' * 70)
        for i, dept in enumerate(depts):
            slug = DEPT_DISPLAY.get(dept.id, (dept.name, f'dept{dept.id}'))[1]
            for suffix, role_label in [
                ('_worker1', 'Сотрудник'),
                ('_worker2', 'Сотрудник'),
                ('_manager', 'Руководитель'),
            ]:
                username = slug + suffix
                self.stdout.write(f'{username:<30} {role_label:<20} {dept.name}')
        self.stdout.write('-' * 70)
        self.stdout.write(f'Пароль для всех: {PASSWORD}')
        self.stdout.write('-' * 70 + '\n')
