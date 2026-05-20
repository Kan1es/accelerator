"""
Django settings for vector project.
"""
import os
from pathlib import Path
import dotenv

# BASE_DIR = vector/  (родитель vector/vector/)
BASE_DIR = Path(__file__).resolve().parent.parent

# .env лежит в vector/.env — parent.parent от vector/vector/settings.py
info = dotenv.dotenv_values(BASE_DIR / ".env")

SECRET_KEY = info['SECRET_KEY']

DEBUG = True

ALLOWED_HOSTS = []


INSTALLED_APPS = [
    'main',
    'channels',
    'rest_framework',
    'drf_yasg',
    'corsheaders',
    'django_celery_beat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    # FIX: CorsMiddleware обязан быть первым — до CommonMiddleware,
    # иначе preflight-запросы браузера не получат CORS-заголовки.
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# FIX: Укажите адреса фронтенда. В проде замените на реальный домен.
# Для быстрой отладки можно временно выставить CORS_ALLOW_ALL_ORIGINS = True.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]
# CORS_ALLOW_ALL_ORIGINS = True  # только для отладки, не использовать в проде

ROOT_URLCONF = 'vector.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Шаблоны лежат в main/templates/ — APP_DIRS=True найдёт их автоматически
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vector.wsgi.application'
ASGI_APPLICATION = 'vector.asgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.getenv('POSTGRES_DB', 'vector'),
        'USER':     os.getenv('POSTGRES_USER', 'vector'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'HOST':     os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT':     os.getenv('POSTGRES_PORT', '5432'),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Django Channels (Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(
                os.getenv('REDIS_HOST', '127.0.0.1'),
                int(os.getenv('REDIS_PORT', '6379')),
            )],
        },
    },
}

# ML Service (FastAPI в ml_service/app.py, порт задаётся в .env)
ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://ml-service:8000')
ML_FEEDBACK_TIMEOUT = int(os.getenv('ML_FEEDBACK_TIMEOUT', '5'))
ML_PREDICT_TIMEOUT = int(os.getenv('ML_PREDICT_TIMEOUT', '3'))
ML_DEFAULT_CATEGORY_ID = int(os.getenv('ML_DEFAULT_CATEGORY_ID', '1'))
ML_STATS_TIMEOUT = int(os.getenv('ML_STATS_TIMEOUT', '5'))