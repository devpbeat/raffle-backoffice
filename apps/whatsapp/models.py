from django.db import models
from django.utils import timezone


class ContactState(models.TextChoices):
    IDLE = 'IDLE', 'Idle'
    BROWSING = 'BROWSING', 'Browsing Raffles'
    SELECTING_NUMBERS = 'SELECTING_NUMBERS', 'Selecting Numbers'
    CONFIRMING_ORDER = 'CONFIRMING_ORDER', 'Confirming Order'
    AWAITING_PAYMENT = 'AWAITING_PAYMENT', 'Awaiting Payment'
    UPLOADING_PROOF = 'UPLOADING_PROOF', 'Uploading Payment Proof'


class WhatsAppContact(models.Model):
    wa_id = models.CharField(max_length=50, unique=True, db_index=True, verbose_name='WhatsApp ID')
    name = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(
        max_length=30,
        choices=ContactState.choices,
        default=ContactState.IDLE,
        db_index=True
    )
    context = models.JSONField(default=dict, blank=True)
    last_interaction_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'WhatsApp Contact'
        verbose_name_plural = 'WhatsApp Contacts'
        ordering = ['-last_interaction_at']
        indexes = [
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
    TEXT = 'text', 'Text'
    IMAGE = 'image', 'Image'
    DOCUMENT = 'document', 'Document'
    AUDIO = 'audio', 'Audio'
    VIDEO = 'video', 'Video'
    STICKER = 'sticker', 'Sticker'
    LOCATION = 'location', 'Location'
    CONTACTS = 'contacts', 'Contacts'
    INTERACTIVE = 'interactive', 'Interactive'
    BUTTON = 'button', 'Button'
    UNKNOWN = 'unknown', 'Unknown'


class InboundMessage(models.Model):
    wa_message_id = models.CharField(max_length=255, unique=True, db_index=True, verbose_name='WhatsApp Message ID')
    contact = models.ForeignKey(
        WhatsAppContact,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    msg_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )
    text = models.TextField(null=True, blank=True)
    media_id = models.CharField(max_length=255, null=True, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = 'Inbound Message'
        verbose_name_plural = 'Inbound Messages'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['-received_at']),
            models.Index(fields=['contact', '-received_at']),
            models.Index(fields=['processed', '-received_at']),
        ]

    def __str__(self):
        return f"{self.contact.wa_id} - {self.msg_type} - {self.received_at.strftime('%Y-%m-%d %H:%M')}"
