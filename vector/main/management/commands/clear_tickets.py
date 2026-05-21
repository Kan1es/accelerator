from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import (
    Ticket, TicketAssignment, TaskQueue, Notification, Employee,
)


class Command(BaseCommand):
    help = (
        "Удаляет все тикеты и связанные с ними записи "
        "(TicketAssignment, TaskQueue, Notification), сбрасывает is_busy у сотрудников. "
        "Сотрудники, отделы, роли, категории, пользователи — сохраняются."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes', action='store_true',
            help='Не запрашивать подтверждение.',
        )

    def handle(self, *args, **options):
        ticket_count = Ticket.objects.count()
        assignment_count = TicketAssignment.objects.count()
        queue_count = TaskQueue.objects.count()
        notif_count = Notification.objects.count()
        busy_count = Employee.objects.filter(is_busy=True).count()

        self.stdout.write(f'Будет удалено:')
        self.stdout.write(f'  - Ticket: {ticket_count}')
        self.stdout.write(f'  - TicketAssignment: {assignment_count}')
        self.stdout.write(f'  - TaskQueue: {queue_count}')
        self.stdout.write(f'  - Notification: {notif_count}')
        self.stdout.write(f'Сбросить is_busy у сотрудников: {busy_count}')

        if not options['yes']:
            answer = input('Продолжить? [y/N]: ').strip().lower()
            if answer != 'y':
                self.stdout.write(self.style.WARNING('Отменено.'))
                return

        with transaction.atomic():
            TaskQueue.objects.all().delete()
            TicketAssignment.objects.all().delete()
            Notification.objects.all().delete()
            Ticket.objects.all().delete()
            Employee.objects.filter(is_busy=True).update(is_busy=False)

        self.stdout.write(self.style.SUCCESS('OK: тикеты очищены.'))
