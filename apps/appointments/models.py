from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import timedelta


class Service(models.Model):
    """
    Tenant-defined services available for booking.
    Examples: Haircut, Consultation, Massage, etc.
    """
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name=_('tenant'),
        db_index=True
    )

    # Service details
    name = models.CharField(_('nombre'), max_length=255)
    description = models.TextField(_('descripción'), blank=True)
    duration_minutes = models.IntegerField(
        _('duración (minutos)'),
        validators=[MinValueValidator(5)],
        help_text=_('Duración del servicio en minutos')
    )
    price = models.DecimalField(
        _('precio'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(_('moneda'), max_length=3, default='USD')

    # Availability settings
    is_active = models.BooleanField(_('activo'), default=True, db_index=True)
    buffer_time_minutes = models.IntegerField(
        _('tiempo de buffer (minutos)'),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Tiempo de preparación antes/después de la cita')
    )
    max_bookings_per_day = models.IntegerField(
        _('máximo de reservas por día'),
        default=20,
        validators=[MinValueValidator(1)],
        help_text=_('Número máximo de citas de este servicio por día')
    )
    advance_booking_days = models.IntegerField(
        _('días de anticipación'),
        default=30,
        validators=[MinValueValidator(1)],
        help_text=_('Cuántos días de anticipación se puede reservar')
    )

    # Timestamps
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)

    class Meta:
        verbose_name = _('Servicio')
        verbose_name_plural = _('Servicios')
        ordering = ['tenant', 'name']
        unique_together = [['tenant', 'name']]
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['tenant', '-created_at']),
        ]

    def __str__(self):
        return f"{self.tenant.slug} - {self.name}"


class Customer(models.Model):
    """
    Customer model for appointments.
    Separate from WhatsAppContact as appointments might come from different channels.
    """
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='customers',
        verbose_name=_('tenant'),
        db_index=True
    )

    # Contact information
    name = models.CharField(_('nombre'), max_length=255)
    email = models.EmailField(_('email'), blank=True)
    phone = models.CharField(_('teléfono'), max_length=50)

    # Additional information
    notes = models.TextField(_('notas'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)
    last_appointment_at = models.DateTimeField(
        _('última cita'),
        null=True,
        blank=True,
        help_text=_('Fecha de la última cita completada')
    )

    class Meta:
        verbose_name = _('Cliente')
        verbose_name_plural = _('Clientes')
        ordering = ['tenant', 'name']
        indexes = [
            models.Index(fields=['tenant', 'phone']),
            models.Index(fields=['tenant', 'email']),
            models.Index(fields=['tenant', '-last_appointment_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class AppointmentStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pendiente')
    CONFIRMED = 'CONFIRMED', _('Confirmado')
    CANCELLED = 'CANCELLED', _('Cancelado')
    COMPLETED = 'COMPLETED', _('Completado')
    NO_SHOW = 'NO_SHOW', _('No Show')


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pendiente')
    PAID = 'PAID', _('Pagado')
    REFUNDED = 'REFUNDED', _('Reembolsado')


class Appointment(models.Model):
    """
    Main appointment model for booking services.
    """
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name=_('tenant'),
        db_index=True
    )

    # Appointment details
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name=_('servicio')
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name=_('cliente')
    )

    # Scheduling
    scheduled_at = models.DateTimeField(_('fecha programada'), db_index=True)
    duration_minutes = models.IntegerField(
        _('duración (minutos)'),
        help_text=_('Duración denormalizada del servicio')
    )

    # Status tracking
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
        db_index=True
    )

    # Payment information
    payment_status = models.CharField(
        _('estado de pago'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    total_amount = models.DecimalField(
        _('monto total'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(_('moneda'), max_length=3, default='USD')
    payment_proof_media_id = models.CharField(
        _('ID de comprobante de pago'),
        max_length=255,
        blank=True,
        null=True
    )

    # Integration IDs
    bancard_transaction_id = models.CharField(
        _('ID transacción Bancard'),
        max_length=255,
        blank=True,
        null=True,
        db_index=True
    )
    google_calendar_event_id = models.CharField(
        _('ID evento Google Calendar'),
        max_length=255,
        blank=True,
        null=True
    )

    # Notes
    customer_notes = models.TextField(_('notas del cliente'), blank=True)
    internal_notes = models.TextField(_('notas internas'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)
    confirmed_at = models.DateTimeField(_('fecha de confirmación'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('fecha de cancelación'), null=True, blank=True)
    completed_at = models.DateTimeField(_('fecha de completado'), null=True, blank=True)

    class Meta:
        verbose_name = _('Cita')
        verbose_name_plural = _('Citas')
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['tenant', 'scheduled_at']),
            models.Index(fields=['tenant', 'status', 'scheduled_at']),
            models.Index(fields=['service', 'scheduled_at']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['status', 'payment_status']),
        ]

    def __str__(self):
        return f"{self.customer.name} - {self.service.name} - {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def end_time(self):
        """Calculate the end time of the appointment."""
        if self.scheduled_at and self.duration_minutes:
            return self.scheduled_at + timedelta(minutes=self.duration_minutes)
        return None

    def save(self, *args, **kwargs):
        # Denormalize service duration and price if creating
        if not self.pk and not self.duration_minutes:
            self.duration_minutes = self.service.duration_minutes
        if not self.pk and not self.total_amount:
            self.total_amount = self.service.price
            self.currency = self.service.currency
        super().save(*args, **kwargs)
