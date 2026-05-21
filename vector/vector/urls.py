"""
URL configuration for vector project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from vector import settings

schema_view = get_schema_view(
    openapi.Info(
        title="Your API",
        default_version='v1',
        description="Your API description",
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(email="contact@yourapp.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def _page(name):
    return TemplateView.as_view(template_name=f'VECTOR/{name}')


# Каталог, где лежат scripts/, styles/, images/ фронта.
_FRONT_ROOT = settings.BASE_DIR / 'main' / 'templates' / 'VECTOR'


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # ── HTML-страницы (фронт) ────────────────────────────────────────────
    path('', _page('index.html')),
    path('index.html', _page('index.html')),
    path('login.html', _page('login.html')),
    path('chat.html', _page('chat.html')),
    path('support.html', _page('support.html')),
    path('employee_dashboard.html', _page('employee_dashboard.html')),
    path('employee_support.html', _page('employee_support.html')),
    path('employee_tasks.html', _page('employee_tasks.html')),
    path('manager_dashboard.html', _page('manager_dashboard.html')),
    path('manager_support.html', _page('manager_support.html')),
    path('manager_tasks.html', _page('manager_tasks.html')),
    path('manager_workers.html', _page('manager_workers.html')),

    # ── Статика фронта (scripts/styles/images доступны как /scripts/...) ─
    re_path(r'^scripts/(?P<path>.*)$', serve, {'document_root': _FRONT_ROOT / 'scripts'}),
    re_path(r'^styles/(?P<path>.*)$',  serve, {'document_root': _FRONT_ROOT / 'styles'}),
    re_path(r'^images/(?P<path>.*)$',  serve, {'document_root': _FRONT_ROOT / 'images'}),

    path('', include('main.urls')),
]



