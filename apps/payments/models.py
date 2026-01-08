from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class PaymentProvider(models.TextChoices):
    BANCARD = 'BANCARD', _('Bancard')
    MANUAL = 'MANUAL', _('Manual')


class PaymentTransaction(models.Model):
    """
    Generic payment transaction model for both raffles and appointments.
    Uses Django's generic foreign key to link to either Order or Appointment.
    """
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='payment_transactions',
        verbose_name=_('tenant'),
        db_index=True
    )

    # Provider information
    provider = models.CharField(
        _('proveedor'),
        max_length=20,
        choices=PaymentProvider.choices,
        default=PaymentProvider.MANUAL
    )

    # Transaction details
    external_id = models.CharField(
        _('ID externo'),
        max_length=255,
        db_index=True,
        help_text=_('ID de la transacción en el proveedor de pago')
    )
    amount = models.DecimalField(
        _('monto'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(_('moneda'), max_length=3, default='USD')
    status = models.CharField(
        _('estado'),
        max_length=20,
        db_index=True,
        help_text=_('Estado de la transacción: pending, paid, failed, refunded')
    )

    # Polymorphic linking - can link to Order or Appointment
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('tipo de contenido')
    )
    object_id = models.PositiveIntegerField(_('ID del objeto'))
    content_object = GenericForeignKey('content_type', 'object_id')

    # Additional data
    raw_response = models.JSONField(
        _('respuesta cruda'),
        default=dict,
        blank=True,
        help_text=_('Respuesta completa del proveedor de pago')
    )
    notes = models.TextField(_('notas'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)
    confirmed_at = models.DateTimeField(_('fecha de confirmación'), null=True, blank=True)

    class Meta:
        verbose_name = _('Transacción de Pago')
        verbose_name_plural = _('Transacciones de Pago')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', '-created_at']),
            models.Index(fields=['external_id']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.provider} - {self.external_id} - {self.status}"
