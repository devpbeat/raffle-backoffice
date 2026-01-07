from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class Raffle(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ticket_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True, db_index=True)
    min_number = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    max_number = models.IntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    draw_date = models.DateTimeField(null=True, blank=True)
    winner_number = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Raffle'
        verbose_name_plural = 'Raffles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.currency} {self.ticket_price})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.max_number < self.min_number:
            raise ValidationError('max_number must be greater than or equal to min_number')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_tickets(self):
        return self.max_number - self.min_number + 1

    @property
    def available_count(self):
        return self.tickets.filter(status=TicketStatus.AVAILABLE).count()

    @property
    def sold_count(self):
        return self.tickets.filter(status=TicketStatus.SOLD).count()

    @property
    def reserved_count(self):
        return self.tickets.filter(status=TicketStatus.RESERVED).count()


class TicketStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    RESERVED = 'RESERVED', 'Reserved'
    SOLD = 'SOLD', 'Sold'


class TicketNumber(models.Model):
    raffle = models.ForeignKey(
        Raffle,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    number = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.AVAILABLE,
        db_index=True
    )
    reserved_by_order = models.ForeignKey(
        'Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reserved_tickets'
    )
    reserved_until = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ticket Number'
        verbose_name_plural = 'Ticket Numbers'
        ordering = ['raffle', 'number']
        unique_together = [['raffle', 'number']]
        indexes = [
            models.Index(fields=['raffle', 'status']),
            models.Index(fields=['status', 'reserved_until']),
        ]

    def __str__(self):
        return f"{self.raffle.title} - #{self.number} ({self.status})"

    def is_reservation_expired(self):
        if self.status == TicketStatus.RESERVED and self.reserved_until:
            return timezone.now() > self.reserved_until
        return False

    def release_if_expired(self):
        if self.is_reservation_expired():
            self.status = TicketStatus.AVAILABLE
            self.reserved_by_order = None
            self.reserved_until = None
            self.save(update_fields=['status', 'reserved_by_order', 'reserved_until', 'updated_at'])
            return True
        return False


class OrderStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
    PAID = 'PAID', 'Paid'
    CANCELLED = 'CANCELLED', 'Cancelled'
    EXPIRED = 'EXPIRED', 'Expired'


class Order(models.Model):
    raffle = models.ForeignKey(
        Raffle,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    contact = models.ForeignKey(
        'whatsapp.WhatsAppContact',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    qty = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)])
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
        db_index=True
    )
    payment_proof_media_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['contact', '-created_at']),
            models.Index(fields=['raffle', '-created_at']),
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.contact.wa_id} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.raffle.ticket_price * self.qty
        super().save(*args, **kwargs)

    def is_expired(self):
        if self.status == OrderStatus.PENDING_PAYMENT and self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def mark_as_expired(self):
        if self.is_expired() and self.status == OrderStatus.PENDING_PAYMENT:
            self.status = OrderStatus.EXPIRED
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

    @property
    def ticket_numbers(self):
        return [ot.ticket.number for ot in self.order_tickets.select_related('ticket').order_by('ticket__number')]


class OrderTicket(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_tickets'
    )
    ticket = models.ForeignKey(
        TicketNumber,
        on_delete=models.CASCADE,
        related_name='order_tickets'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Order Ticket'
        verbose_name_plural = 'Order Tickets'
        unique_together = [['order', 'ticket']]
        indexes = [
            models.Index(fields=['order', 'ticket']),
        ]

    def __str__(self):
        return f"Order #{self.order.id} - Ticket #{self.ticket.number}"
