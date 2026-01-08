from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from apps.whatsapp.models import WhatsAppContact, InboundMessage


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    list_display = [
        'wa_id',
        'name',
        'state_badge',
        'last_interaction_at',
        'created_at',
    ]
    list_filter = ['state', 'created_at', 'last_interaction_at']
    search_fields = ['wa_id', 'name']
    readonly_fields = ['created_at', 'updated_at', 'last_interaction_at']
    ordering = ['-last_interaction_at']

    fieldsets = (
        (_('Información del Contacto'), {
            'fields': ('wa_id', 'name')
        }),
        (_('Estado y Contexto'), {
            'fields': ('state', 'context')
        }),
        (_('Fechas'), {
            'fields': ('last_interaction_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Estado'))
    def state_badge(self, obj):
        colors = {
            'IDLE': 'gray',
            'BROWSING': 'blue',
            'SELECTING_NUMBERS': 'orange',
            'CONFIRMING_ORDER': 'purple',
            'AWAITING_PAYMENT': 'yellow',
            'UPLOADING_PROOF': 'green',
        }
        color = colors.get(obj.state, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_state_display()
        )


@admin.register(InboundMessage)
class InboundMessageAdmin(admin.ModelAdmin):
    list_display = [
        'wa_message_id',
        'contact_display',
        'msg_type',
        'text_preview',
        'processed',
        'received_at',
    ]
    list_filter = ['msg_type', 'processed', 'received_at']
    search_fields = ['wa_message_id', 'contact__wa_id', 'contact__name', 'text']
    readonly_fields = ['received_at']
    ordering = ['-received_at']
    date_hierarchy = 'received_at'

    fieldsets = (
        (_('Información del Mensaje'), {
            'fields': ('wa_message_id', 'contact', 'msg_type', 'text', 'media_id')
        }),
        (_('Procesamiento'), {
            'fields': ('processed', 'received_at')
        }),
        (_('Datos Crudos'), {
            'fields': ('raw_payload',),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Contacto'))
    def contact_display(self, obj):
        return obj.contact.name or obj.contact.wa_id

    @admin.display(description=_('Vista Previa'))
    def text_preview(self, obj):
        if obj.text:
            preview = obj.text[:50]
            return preview + '...' if len(obj.text) > 50 else preview
        return '-'
