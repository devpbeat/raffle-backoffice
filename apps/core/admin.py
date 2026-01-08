from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.core.models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['slug', 'name', 'is_active', 'plan', 'created_at']
    list_filter = ['is_active', 'plan', 'created_at']
    search_fields = ['slug', 'name', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        (_('Información Básica'), {
            'fields': ('slug', 'name', 'is_active')
        }),
        (_('Contacto'), {
            'fields': ('contact_email', 'contact_phone', 'logo_url')
        }),
        (_('Plan y Límites'), {
            'fields': ('plan', 'max_appointments_per_month', 'max_raffles')
        }),
        (_('Configuración'), {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Only superusers can create tenants
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Only superusers can edit tenants
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete tenants
        return request.user.is_superuser
