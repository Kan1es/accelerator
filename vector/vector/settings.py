"""
Django settings for vector project.
"""
import os
from pathlib import Path
import dotenv

# BASE_DIR = vector/  (родитель vector/vector/)
BASE_DIR = Path(__file__).resolve().parent.parent

# .env лежит в vector/.env. Подгружаем в os.environ, чтобы os.getenv ниже работал.
dotenv.load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


INSTALLED_APPS = [
    'main',
    'channels',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'django_celery_beat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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

STATIC_URL = '/static/'
# Раздаём JS/CSS/картинки фронта из main/templates/VECTOR/.
# В шаблонах ссылки остаются относительными (scripts/..., styles/..., images/...),
# а Django отдаёт эти каталоги статикой под /static/.
STATICFILES_DIRS = [
    BASE_DIR / 'main' / 'templates' / 'VECTOR',
]
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