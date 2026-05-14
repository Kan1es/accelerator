import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vector.settings')

app = Celery('vector')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check_timeouts': {
        'task': 'main.tasks.check_timeouts',
        'schedule': 60.0,  # 60 секунд
    },
    'cleanup_end_of_day': {
        'task': 'your_app.tasks.cleanup_end_of_day',
        'schedule': crontab(minute=0, hour=0),  # 00:00
    },

    'remind_last_employee': {
        'task': 'your_app.tasks.remind_last_employee',
        'schedule': 15 * 60.0,  # 15 минут в секундах
    },
    'check_escalation': {
        'task': 'main.tasks.check_escalation',
        'schedule': 300.0,
    },
    'remind_deadline': {
        'task': 'main.tasks.remind_deadline',
        'schedule': 900.0,
    }
}

app.conf.timezone = 'UTC'