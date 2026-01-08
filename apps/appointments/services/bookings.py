from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from apps.appointments.models import (
    Appointment,
    AppointmentStatus,
    PaymentStatus,
    Service,
    Customer
)


class BookingError(Exception):
    """Exception raised for booking-related errors."""
    pass


@transaction.atomic
def create_appointment(tenant, service_id, customer_data, scheduled_at, notes=''):
    """
    Create a new appointment with availability checking.

    Args:
        tenant: Tenant instance
        service_id: ID of the service
        customer_data: dict with 'name', 'phone', and optionally 'email'
        scheduled_at: datetime for the appointment
        notes: customer notes (optional)

    Returns:
        Appointment instance

    Raises:
        BookingError: If slot not available or validation fails
    """
    # Get service with lock
    try:
        service = Service.objects.select_for_update().get(
            id=service_id,
            tenant=tenant,
            is_active=True
        )
    except Service.DoesNotExist:
        raise BookingError("Servicio no encontrado o inactivo")

    # Validate scheduled time is in the future
    if scheduled_at <= timezone.now():
        raise BookingError("No se pueden reservar citas en el pasado")

    # Check if appointment is within advance booking window
    max_advance = timezone.now() + timedelta(days=service.advance_booking_days)
    if scheduled_at > max_advance:
        raise BookingError(
            f"No se puede reservar con más de {service.advance_booking_days} días de anticipación"
        )

    # Check availability
    if not is_slot_available(tenant, service, scheduled_at):
        raise BookingError("Este horario no está disponible")

    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        tenant=tenant,
        phone=customer_data['phone'],
        defaults={
            'name': customer_data['name'],
            'email': customer_data.get('email', ''),
        }
    )

    # Update customer name if provided and different
    if not created and customer_data.get('name') and customer.name != customer_data['name']:
        customer.name = customer_data['name']
        if customer_data.get('email'):
            customer.email = customer_data['email']
        customer.save(update_fields=['name', 'email', 'updated_at'])

    # Create appointment
    appointment = Appointment.objects.create(
        tenant=tenant,
        service=service,
        customer=customer,
        scheduled_at=scheduled_at,
        duration_minutes=service.duration_minutes,
        total_amount=service.price,
        currency=service.currency,
        status=AppointmentStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        customer_notes=notes
    )

    return appointment


def is_slot_available(tenant, service, scheduled_at):
    """
    Check if a time slot is available for booking.

    Args:
        tenant: Tenant instance
        service: Service instance
        scheduled_at: datetime to check

    Returns:
        bool: True if slot is available, False otherwise
    """
    end_time = scheduled_at + timedelta(minutes=service.duration_minutes)
    buffer = timedelta(minutes=service.buffer_time_minutes)

    # Check for overlapping appointments (with buffer)
    # An appointment overlaps if it starts before this one ends (plus buffer)
    # and ends after this one starts (minus buffer)
    overlapping = Appointment.objects.filter(
        tenant=tenant,
        service=service,
        status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED],
    ).exclude(
        # Exclude appointments that end before our start time (with buffer)
        scheduled_at__lt=scheduled_at - timedelta(minutes=service.duration_minutes) - buffer
    ).exclude(
        # Exclude appointments that start after our end time (with buffer)
        scheduled_at__gte=end_time + buffer
    ).exists()

    if overlapping:
        return False

    # Check daily booking limit for this service
    day_start = scheduled_at.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    daily_count = Appointment.objects.filter(
        tenant=tenant,
        service=service,
        scheduled_at__gte=day_start,
        scheduled_at__lt=day_end,
        status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]
    ).count()

    if daily_count >= service.max_bookings_per_day:
        return False

    return True


@transaction.atomic
def confirm_appointment(appointment, payment_transaction_id=None):
    """
    Confirm an appointment after payment verification.

    Args:
        appointment: Appointment instance
        payment_transaction_id: Optional payment transaction ID (from Bancard)

    Returns:
        Updated Appointment instance

    Raises:
        BookingError: If appointment cannot be confirmed
    """
    if appointment.status != AppointmentStatus.PENDING:
        raise BookingError(
            f"No se puede confirmar una cita con estado: {appointment.get_status_display()}"
        )

    # Update appointment status
    appointment.status = AppointmentStatus.CONFIRMED
    appointment.payment_status = PaymentStatus.PAID
    appointment.confirmed_at = timezone.now()

    if payment_transaction_id:
        appointment.bancard_transaction_id = payment_transaction_id

    appointment.save(update_fields=[
        'status',
        'payment_status',
        'confirmed_at',
        'bancard_transaction_id',
        'updated_at'
    ])

    # Update customer's last appointment date
    appointment.customer.last_appointment_at = timezone.now()
    appointment.customer.save(update_fields=['last_appointment_at', 'updated_at'])

    return appointment


@transaction.atomic
def cancel_appointment(appointment, reason=''):
    """
    Cancel an appointment.

    Args:
        appointment: Appointment instance
        reason: Reason for cancellation (optional)

    Returns:
        Updated Appointment instance

    Raises:
        BookingError: If appointment cannot be cancelled
    """
    if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
        raise BookingError(
            f"No se puede cancelar una cita con estado: {appointment.get_status_display()}"
        )

    # Update appointment status
    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = timezone.now()

    # Add cancellation reason to internal notes
    if reason:
        if appointment.internal_notes:
            appointment.internal_notes += f"\n\nCancelado: {reason}"
        else:
            appointment.internal_notes = f"Cancelado: {reason}"

    appointment.save(update_fields=[
        'status',
        'cancelled_at',
        'internal_notes',
        'updated_at'
    ])

    return appointment


@transaction.atomic
def complete_appointment(appointment):
    """
    Mark an appointment as completed.

    Args:
        appointment: Appointment instance

    Returns:
        Updated Appointment instance

    Raises:
        BookingError: If appointment cannot be completed
    """
    if appointment.status != AppointmentStatus.CONFIRMED:
        raise BookingError(
            f"Solo se pueden completar citas confirmadas. Estado actual: {appointment.get_status_display()}"
        )

    # Check if appointment time has passed
    if appointment.end_time > timezone.now():
        raise BookingError("No se puede completar una cita que aún no ha terminado")

    appointment.status = AppointmentStatus.COMPLETED
    appointment.completed_at = timezone.now()

    appointment.save(update_fields=[
        'status',
        'completed_at',
        'updated_at'
    ])

    # Update customer's last completed appointment
    appointment.customer.last_appointment_at = appointment.completed_at
    appointment.customer.save(update_fields=['last_appointment_at', 'updated_at'])

    return appointment


@transaction.atomic
def mark_no_show(appointment):
    """
    Mark an appointment as no-show (customer didn't attend).

    Args:
        appointment: Appointment instance

    Returns:
        Updated Appointment instance

    Raises:
        BookingError: If appointment cannot be marked as no-show
    """
    if appointment.status != AppointmentStatus.CONFIRMED:
        raise BookingError(
            f"Solo se pueden marcar como 'no show' citas confirmadas. Estado actual: {appointment.get_status_display()}"
        )

    # Check if appointment time has passed
    if appointment.scheduled_at > timezone.now():
        raise BookingError("No se puede marcar como 'no show' una cita futura")

    appointment.status = AppointmentStatus.NO_SHOW
    appointment.internal_notes += f"\n\nMarcado como No Show el {timezone.now().strftime('%Y-%m-%d %H:%M')}"

    appointment.save(update_fields=[
        'status',
        'internal_notes',
        'updated_at'
    ])

    return appointment
