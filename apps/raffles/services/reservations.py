import random
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from apps.raffles.models import (
    Raffle,
    TicketNumber,
    TicketStatus,
    Order,
    OrderStatus,
    OrderTicket,
)


class ReservationError(Exception):
    pass


def _get_reservation_timeout():
    return timezone.now() + timedelta(minutes=settings.RESERVATION_TIMEOUT_MINUTES)


def _validate_quantity(qty):
    if qty < settings.MIN_TICKETS_PER_ORDER:
        raise ReservationError(f"Minimum {settings.MIN_TICKETS_PER_ORDER} ticket(s) required")
    if qty > settings.MAX_TICKETS_PER_ORDER:
        raise ReservationError(f"Maximum {settings.MAX_TICKETS_PER_ORDER} tickets allowed")


@transaction.atomic
def reserve_specific(raffle_id, numbers, contact):
    """
    Reserve specific ticket numbers for a contact.

    Args:
        raffle_id: ID of the raffle
        numbers: List of ticket numbers to reserve
        contact: WhatsAppContact instance

    Returns:
        Order instance

    Raises:
        ReservationError: If tickets are not available or validation fails
    """
    try:
        raffle = Raffle.objects.select_for_update().get(id=raffle_id, is_active=True)
    except Raffle.DoesNotExist:
        raise ReservationError("Raffle not found or is not active")

    qty = len(numbers)
    _validate_quantity(qty)

    # Validate all numbers are within range
    invalid_numbers = [n for n in numbers if n < raffle.min_number or n > raffle.max_number]
    if invalid_numbers:
        raise ReservationError(f"Invalid numbers: {', '.join(map(str, invalid_numbers))}")

    # Check for duplicates
    if len(numbers) != len(set(numbers)):
        raise ReservationError("Duplicate numbers are not allowed")

    # Release expired reservations first
    TicketNumber.objects.filter(
        raffle=raffle,
        status=TicketStatus.RESERVED,
        reserved_until__lt=timezone.now()
    ).update(
        status=TicketStatus.AVAILABLE,
        reserved_by_order=None,
        reserved_until=None
    )

    # Lock and verify availability
    tickets = list(
        TicketNumber.objects.select_for_update()
        .filter(raffle=raffle, number__in=numbers)
    )

    if len(tickets) != qty:
        missing = set(numbers) - {t.number for t in tickets}
        raise ReservationError(f"Tickets not found: {', '.join(map(str, missing))}")

    unavailable = [t.number for t in tickets if t.status != TicketStatus.AVAILABLE]
    if unavailable:
        raise ReservationError(f"Tickets not available: {', '.join(map(str, unavailable))}")

    # Create order
    total_amount = raffle.ticket_price * qty
    expires_at = _get_reservation_timeout()

    order = Order.objects.create(
        raffle=raffle,
        contact=contact,
        qty=qty,
        total_amount=total_amount,
        status=OrderStatus.PENDING_PAYMENT,
        expires_at=expires_at
    )

    # Reserve tickets
    for ticket in tickets:
        ticket.status = TicketStatus.RESERVED
        ticket.reserved_by_order = order
        ticket.reserved_until = expires_at
        ticket.save(update_fields=['status', 'reserved_by_order', 'reserved_until', 'updated_at'])

        OrderTicket.objects.create(order=order, ticket=ticket)

    return order


@transaction.atomic
def reserve_random(raffle_id, qty, contact):
    """
    Reserve random available ticket numbers.

    Args:
        raffle_id: ID of the raffle
        qty: Number of tickets to reserve
        contact: WhatsAppContact instance

    Returns:
        Order instance

    Raises:
        ReservationError: If not enough tickets available or validation fails
    """
    try:
        raffle = Raffle.objects.select_for_update().get(id=raffle_id, is_active=True)
    except Raffle.DoesNotExist:
        raise ReservationError("Raffle not found or is not active")

    _validate_quantity(qty)

    # Release expired reservations first
    TicketNumber.objects.filter(
        raffle=raffle,
        status=TicketStatus.RESERVED,
        reserved_until__lt=timezone.now()
    ).update(
        status=TicketStatus.AVAILABLE,
        reserved_by_order=None,
        reserved_until=None
    )

    # Get available tickets (SQLite-safe: fetch all, then random select in Python)
    available_tickets = list(
        TicketNumber.objects.select_for_update()
        .filter(raffle=raffle, status=TicketStatus.AVAILABLE)
    )

    if len(available_tickets) < qty:
        raise ReservationError(
            f"Only {len(available_tickets)} ticket(s) available, you requested {qty}"
        )

    # Random selection in Python (SQLite-safe)
    selected_tickets = random.sample(available_tickets, qty)

    # Create order
    total_amount = raffle.ticket_price * qty
    expires_at = _get_reservation_timeout()

    order = Order.objects.create(
        raffle=raffle,
        contact=contact,
        qty=qty,
        total_amount=total_amount,
        status=OrderStatus.PENDING_PAYMENT,
        expires_at=expires_at
    )

    # Reserve tickets
    for ticket in selected_tickets:
        ticket.status = TicketStatus.RESERVED
        ticket.reserved_by_order = order
        ticket.reserved_until = expires_at
        ticket.save(update_fields=['status', 'reserved_by_order', 'reserved_until', 'updated_at'])

        OrderTicket.objects.create(order=order, ticket=ticket)

    return order


@transaction.atomic
def release_order_reservations(order):
    """
    Release all tickets reserved by an order.

    Args:
        order: Order instance

    Returns:
        Number of tickets released
    """
    if order.status not in [OrderStatus.DRAFT, OrderStatus.PENDING_PAYMENT, OrderStatus.EXPIRED]:
        raise ReservationError(f"Cannot release tickets for order with status: {order.status}")

    tickets = TicketNumber.objects.filter(reserved_by_order=order)
    count = tickets.count()

    tickets.update(
        status=TicketStatus.AVAILABLE,
        reserved_by_order=None,
        reserved_until=None
    )

    order.status = OrderStatus.CANCELLED
    order.save(update_fields=['status', 'updated_at'])

    return count


@transaction.atomic
def confirm_paid(order, payment_proof_media_id=None):
    """
    Confirm payment and mark tickets as sold.

    Args:
        order: Order instance
        payment_proof_media_id: Optional media ID of payment proof

    Returns:
        Updated Order instance

    Raises:
        ReservationError: If order cannot be confirmed
    """
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise ReservationError(f"Cannot confirm order with status: {order.status}")

    # Mark all reserved tickets as sold
    tickets = TicketNumber.objects.filter(reserved_by_order=order)

    if not tickets.exists():
        raise ReservationError("No tickets found for this order")

    tickets.update(
        status=TicketStatus.SOLD,
        reserved_until=None
    )

    # Update order
    order.status = OrderStatus.PAID
    order.paid_at = timezone.now()
    if payment_proof_media_id:
        order.payment_proof_media_id = payment_proof_media_id
    order.save(update_fields=['status', 'paid_at', 'payment_proof_media_id', 'updated_at'])

    return order
