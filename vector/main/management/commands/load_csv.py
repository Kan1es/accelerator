import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from main.models import Department, Role, Employee, Category, EscalationRule, Ticket, TicketAssignment
from django.conf import settings

class Command(BaseCommand):
    help = 'Loads data from CSV files into Database'

    def handle(self, *args, **kwargs):
        data_dir = os.path.join(settings.BASE_DIR, 'Data')
        
        def safe_int(val):
            return int(val) if val and val.isdigit() else None
            
        def safe_dt(val):
            if not val:
                return None
            try:
                return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None

        dept_path = os.path.join(data_dir, 'department.csv')
        if os.path.exists(dept_path):
            with open(dept_path, 'r', encoding='utf-8') as f:
                for row in csv.reader(f):
                    Department.objects.get_or_create(
                        id=int(row[0]),
                        defaults={'name': row[1], 'parent_id': safe_int(row[2])}
                    )
            self.stdout.write(self.style.SUCCESS('Departments loaded'))

        role_path = os.path.join(data_dir, 'role.csv')
        if os.path.exists(role_path):
            with open(role_path, 'r', encoding='utf-8') as f:
                for row in csv.reader(f):
                    Role.objects.get_or_create(
                        id=int(row[0]),
                        defaults={'name': row[1], 'power': int(row[2])}
                    )
            self.stdout.write(self.style.SUCCESS('Roles loaded'))

        emp_path = os.path.join(data_dir, 'employees.csv')
        if os.path.exists(emp_path):
            with open(emp_path, 'r', encoding='utf-8') as f:
                for row in csv.reader(f):
                    Employee.objects.get_or_create(
                        id=int(row[0]),
                        defaults={
                            'name': row[1],
                            'role_id': safe_int(row[2]),
                            'department_id': safe_int(row[3]),
                            'is_active': row[4].lower() in ['t', 'true', '1']
                        }
                    )
            self.stdout.write(self.style.SUCCESS('Employees loaded'))

        cat_path = os.path.join(data_dir, 'categories.csv')
        if os.path.exists(cat_path):
            with open(cat_path, 'r', encoding='utf-8') as f:
                for row in csv.reader(f):
                    Category.objects.get_or_create(
                        id=int(row[0]),
                        defaults={
                            'name': row[1],
                            'keywords': row[2],
                            'parent_id': safe_int(row[3])
                        }
                    )
            self.stdout.write(self.style.SUCCESS('Categories loaded'))

        esc_path = os.path.join(data_dir, 'escalation_rules.csv')
        if os.path.exists(esc_path):
            with open(esc_path, 'r', encoding='utf-8') as f:
                for row in csv.reader(f):
                    EscalationRule.objects.get_or_create(
                        id=int(row[0]),
                        defaults={
                            'category_id': int(row[1]),
                            'time_limit': int(row[2])
                        }
                    )
            self.stdout.write(self.style.SUCCESS('Escalation Rules loaded'))

        ticket_path = os.path.join(data_dir, 'tickets.csv')
        if os.path.exists(ticket_path):
            with open(ticket_path, 'r', encoding='utf-8') as f:
                for row in csv.reader(f):
                    Ticket.objects.get_or_create(
                        id=int(row[0]),
                        defaults={
                            'description': row[1],
                            'category_id': safe_int(row[2]),
                            'priority': int(row[3]),
                            'status': row[4],
                            'created_at': safe_dt(row[5]),
                            'creator_id': safe_int(row[6]),
                            'assignee_id': safe_int(row[7]),
                        }
                    )
            self.stdout.write(self.style.SUCCESS('Tickets loaded'))

        assign_path = os.path.join(data_dir, 'ticket_assignments.csv')
        if os.path.exists(assign_path):
            with open(assign_path, 'r', encoding='utf-8') as f:
                for row in csv.reader(f):
                    TicketAssignment.objects.get_or_create(
                        id=int(row[0]),
                        defaults={
                            'ticket_id': int(row[1]),
                            'assignee_id': int(row[2]),
                            'assigner_id': safe_int(row[3]),
                            'assigned_time': safe_dt(row[4]),
                            'resolved_time': safe_dt(row[5]),
                            'is_resolved': row[6].lower() in ['t', 'true', '1']
                        }
                    )
            self.stdout.write(self.style.SUCCESS('Ticket assignments loaded'))
