"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.whatsapp.views import webhook_verify

urlpatterns = [
    # WhatsApp Webhook (tenant-agnostic - Meta sends to specific URL)
    path('whatsapp/webhook/', webhook_verify, name='whatsapp_webhook_verify'),
    path('whatsapp/', include('apps.whatsapp.urls')),

    # Global API Schema & Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Tenant-scoped URLs
    path('tenant/<slug:tenant_slug>/', include([
        # Tenant-scoped API endpoints
        path('api/', include([
            path('raffles/', include('apps.raffles.urls')),
            path('whatsapp/', include('apps.whatsapp.api_urls')),
            path('appointments/', include('apps.appointments.urls')),
            # Future: payments, etc. will be added here
        ])),
    ])),

    # Backward compatibility: Global API endpoints (no tenant) for existing integrations
    # These will use the default tenant or require migration
    path('api/', include('apps.raffles.urls')),
    path('api/whatsapp/', include('apps.whatsapp.api_urls')),

    # i18n language switching
    path('i18n/', include('django.conf.urls.i18n')),
]

# Add i18n support for admin
# Global admin for superusers to manage tenants and cross-tenant operations
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    prefix_default_language=False,
)
