from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from apps.payments.models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'external_id',
        'tenant',
        'provider',
        'amount_display',
        'status_badge',
        'content_type',
        'created_at',
    ]
    list_filter = ['tenant', 'provider', 'status', 'created_at']
    search_fields = ['external_id', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at', 'content_type', 'object_id']

    fieldsets = (
        (_('Información de la Transacción'), {
            'fields': ('tenant', 'provider', 'external_id', 'status')
        }),
        (_('Monto'), {
            'fields': ('amount', 'currency')
        }),
        (_('Objeto Relacionado'), {
            'fields': ('content_type', 'object_id')
        }),
        (_('Detalles'), {
            'fields': ('notes', 'raw_response'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )

    def amount_display(self, obj):
        """Format amount with currency."""
        return f"{obj.currency} {obj.amount}"
    amount_display.short_description = _('Monto')

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#FFA500',  # Orange
            'paid': '#28a745',  # Green
            'failed': '#dc3545',  # Red
            'refunded': '#6c757d',  # Gray
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = _('Estado')
