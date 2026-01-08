from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ContactState(models.TextChoices):
    IDLE = 'IDLE', _('Inactivo')
    BROWSING = 'BROWSING', _('Explorando Rifas')
    SELECTING_NUMBERS = 'SELECTING_NUMBERS', _('Seleccionando Números')
    CONFIRMING_ORDER = 'CONFIRMING_ORDER', _('Confirmando Orden')
    AWAITING_PAYMENT = 'AWAITING_PAYMENT', _('Esperando Pago')
    UPLOADING_PROOF = 'UPLOADING_PROOF', _('Subiendo Comprobante')


class WhatsAppContact(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='whatsapp_contacts',
        verbose_name=_('tenant'),
        db_index=True
    )
    wa_id = models.CharField(_('ID de WhatsApp'), max_length=50, unique=True, db_index=True)
    name = models.CharField(_('nombre'), max_length=255, null=True, blank=True)
    state = models.CharField(
        _('estado'),
        max_length=30,
        choices=ContactState.choices,
        default=ContactState.IDLE,
        db_index=True
    )
    context = models.JSONField(_('contexto'), default=dict, blank=True)
    last_interaction_at = models.DateTimeField(_('última interacción'), default=timezone.now, db_index=True)
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)

    class Meta:
        verbose_name = _('Contacto de WhatsApp')
        verbose_name_plural = _('Contactos de WhatsApp')
        ordering = ['-last_interaction_at']
        indexes = [
            models.Index(fields=['tenant', '-last_interaction_at']),
            models.Index(fields=['-last_interaction_at']),
            models.Index(fields=['state', '-last_interaction_at']),
        ]

    def __str__(self):
        return f"{self.name or self.wa_id} ({self.wa_id})"

    def update_state(self, new_state, context_update=None):
        self.state = new_state
        self.last_interaction_at = timezone.now()
        if context_update:
            self.context.update(context_update)
        self.save(update_fields=['state', 'last_interaction_at', 'context', 'updated_at'])

    def clear_context(self):
        self.context = {}
        self.save(update_fields=['context', 'updated_at'])


class MessageType(models.TextChoices):
    TEXT = 'text', _('Texto')
    IMAGE = 'image', _('Imagen')
    DOCUMENT = 'document', _('Documento')
    AUDIO = 'audio', _('Audio')
    VIDEO = 'video', _('Video')
    STICKER = 'sticker', _('Sticker')
    LOCATION = 'location', _('Ubicación')
    CONTACTS = 'contacts', _('Contactos')
    INTERACTIVE = 'interactive', _('Interactivo')
    BUTTON = 'button', _('Botón')
    UNKNOWN = 'unknown', _('Desconocido')


class InboundMessage(models.Model):
    wa_message_id = models.CharField(_('ID de mensaje de WhatsApp'), max_length=255, unique=True, db_index=True)
    contact = models.ForeignKey(
        WhatsAppContact,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('contacto')
    )
    msg_type = models.CharField(
        _('tipo de mensaje'),
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )
    text = models.TextField(_('texto'), null=True, blank=True)
    media_id = models.CharField(_('ID de media'), max_length=255, null=True, blank=True)
    raw_payload = models.JSONField(_('payload crudo'), default=dict, blank=True)
    received_at = models.DateTimeField(_('fecha de recepción'), auto_now_add=True, db_index=True)
    processed = models.BooleanField(_('procesado'), default=False, db_index=True)

    class Meta:
        verbose_name = _('Mensaje Entrante')
        verbose_name_plural = _('Mensajes Entrantes')
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['-received_at']),
            models.Index(fields=['contact', '-received_at']),
            models.Index(fields=['processed', '-received_at']),
        ]

    def __str__(self):
        return f"{self.contact.wa_id} - {self.msg_type} - {self.received_at.strftime('%Y-%m-%d %H:%M')}"
