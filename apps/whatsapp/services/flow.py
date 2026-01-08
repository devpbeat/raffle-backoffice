import re
import logging
from django.conf import settings
from apps.whatsapp.models import WhatsAppContact, ContactState, InboundMessage
from apps.raffles.models import Raffle, Order, OrderStatus
from apps.raffles.services import (
    reserve_specific,
    reserve_random,
    confirm_paid,
    release_order_reservations,
    ReservationError,
)
from .meta_client import send_text, send_interactive_list, send_interactive_buttons
from . import messages_es as msg

logger = logging.getLogger(__name__)


def process_message(inbound_message):
    """
    Main entry point for processing inbound WhatsApp messages.
    Routes to appropriate handler based on contact state.

    Args:
        inbound_message: InboundMessage instance

    Returns:
        bool: True if processed successfully
    """
    contact = inbound_message.contact
    text = (inbound_message.text or '').strip()

    try:
        # Route based on contact state
        if contact.state == ContactState.IDLE:
            handle_idle(contact, text)
        elif contact.state == ContactState.BROWSING:
            handle_browsing(contact, text)
        elif contact.state == ContactState.SELECTING_NUMBERS:
            handle_selecting_numbers(contact, text)
        elif contact.state == ContactState.CONFIRMING_ORDER:
            handle_confirming_order(contact, text)
        elif contact.state == ContactState.AWAITING_PAYMENT:
            handle_awaiting_payment(contact, text)
        elif contact.state == ContactState.UPLOADING_PROOF:
            handle_uploading_proof(contact, inbound_message)
        else:
            send_text(contact.wa_id, msg.MSG_SOMETHING_WENT_WRONG)
            contact.update_state(ContactState.IDLE)

        inbound_message.processed = True
        inbound_message.save(update_fields=['processed'])
        return True

    except Exception as e:
        logger.error(f"Error processing message for {contact.wa_id}: {e}", exc_info=True)
        send_text(contact.wa_id, msg.MSG_ERROR_OCCURRED)
        contact.update_state(ContactState.IDLE)
        return False


def handle_idle(contact, text):
    """Handle messages when contact is in IDLE state."""
    text_lower = text.lower()

    if text_lower in ['menu', 'start', 'hola', 'inicio', 'ayuda', 'help']:
        show_main_menu(contact)
    elif text_lower in ['rifas', 'raffles', 'browse', 'ver']:
        show_active_raffles(contact)
    else:
        send_text(contact.wa_id, msg.MSG_WELCOME)


def show_main_menu(contact):
    """Show main menu to contact."""
    buttons = [
        {'id': 'browse_raffles', 'title': msg.BTN_BROWSE_RAFFLES},
        {'id': 'my_orders', 'title': msg.BTN_MY_ORDERS},
        {'id': 'help', 'title': msg.BTN_HELP},
    ]

    try:
        send_interactive_buttons(
            contact.wa_id,
            msg.MSG_MAIN_MENU,
            buttons
        )
    except Exception:
        # Fallback to text if interactive fails
        send_text(contact.wa_id, msg.TXT_MENU_OPTIONS)


def show_active_raffles(contact):
    """Show list of active raffles."""
    raffles = Raffle.objects.filter(is_active=True).order_by('-created_at')[:10]

    if not raffles:
        send_text(contact.wa_id, msg.MSG_NO_ACTIVE_RAFFLES)
        return

    message_lines = [msg.MSG_ACTIVE_RAFFLES_HEADER]
    for idx, raffle in enumerate(raffles, 1):
        available = raffle.available_count
        total = raffle.total_tickets
        message_lines.append(
            f"{idx}. *{raffle.title}*\n"
            f"   Precio: {raffle.currency} {raffle.ticket_price}\n"
            f"   Disponibles: {available}/{total}\n"
        )

    message_lines.append(msg.MSG_SELECT_RAFFLE.format(count=len(raffles)))

    send_text(contact.wa_id, "\n".join(message_lines))
    contact.update_state(ContactState.BROWSING, {'raffles': [r.id for r in raffles]})


def handle_browsing(contact, text):
    """Handle raffle selection."""
    if text.lower() == 'menu':
        show_main_menu(contact)
        contact.update_state(ContactState.IDLE)
        return

    try:
        selection = int(text)
        raffle_ids = contact.context.get('raffles', [])

        if 1 <= selection <= len(raffle_ids):
            raffle_id = raffle_ids[selection - 1]
            raffle = Raffle.objects.get(id=raffle_id, is_active=True)
            show_raffle_details(contact, raffle)
        else:
            send_text(contact.wa_id, f"Por favor ingresa un número entre 1 y {len(raffle_ids)}.")

    except (ValueError, Raffle.DoesNotExist):
        send_text(contact.wa_id, msg.MSG_INVALID_SELECTION)


def show_raffle_details(contact, raffle):
    """Show detailed information about a raffle."""
    available = raffle.available_count
    sold = raffle.sold_count
    total = raffle.total_tickets

    message = msg.MSG_RAFFLE_DETAILS.format(
        title=raffle.title,
        description=raffle.description,
        currency=raffle.currency,
        price=raffle.ticket_price,
        min_number=raffle.min_number,
        max_number=raffle.max_number,
        available=available,
        total=total,
        sold=sold
    )

    send_text(contact.wa_id, message)
    contact.update_state(ContactState.SELECTING_NUMBERS, {'raffle_id': raffle.id})


def handle_selecting_numbers(contact, text):
    """Handle ticket number selection."""
    if text.lower() in ['volver', 'back']:
        show_active_raffles(contact)
        return

    if text.lower() == 'menu':
        show_main_menu(contact)
        contact.update_state(ContactState.IDLE)
        return

    raffle_id = contact.context.get('raffle_id')
    if not raffle_id:
        send_text(contact.wa_id, msg.MSG_SESSION_EXPIRED)
        contact.update_state(ContactState.IDLE)
        return

    try:
        raffle = Raffle.objects.get(id=raffle_id, is_active=True)

        # Check if random selection (aleatorio or random)
        random_match = re.match(r'(aleatorio|random)\s+(\d+)', text.lower())
        if random_match:
            qty = int(random_match.group(2))
            create_random_reservation(contact, raffle, qty)
            return

        # Parse specific numbers
        numbers = parse_numbers(text)
        if not numbers:
            send_text(contact.wa_id, msg.MSG_INVALID_NUMBER_FORMAT)
            return

        create_specific_reservation(contact, raffle, numbers)

    except Raffle.DoesNotExist:
        send_text(contact.wa_id, msg.MSG_RAFFLE_NOT_AVAILABLE)
        contact.update_state(ContactState.IDLE)
    except Exception as e:
        logger.error(f"Error in handle_selecting_numbers: {e}")
        send_text(contact.wa_id, msg.MSG_ERROR_OCCURRED)


def create_specific_reservation(contact, raffle, numbers):
    """Create order with specific ticket numbers."""
    try:
        order = reserve_specific(raffle.id, numbers, contact)
        show_order_confirmation(contact, order)
    except ReservationError as e:
        send_text(contact.wa_id, f"❌ {str(e)}{msg.MSG_TRY_DIFFERENT_NUMBERS}")


def create_random_reservation(contact, raffle, qty):
    """Create order with random ticket numbers."""
    try:
        order = reserve_random(raffle.id, qty, contact)
        show_order_confirmation(contact, order)
    except ReservationError as e:
        send_text(contact.wa_id, f"❌ {str(e)}{msg.MSG_TRY_DIFFERENT_QUANTITY}")


def show_order_confirmation(contact, order):
    """Show order details and ask for confirmation."""
    numbers = order.ticket_numbers
    numbers_str = ', '.join(map(str, numbers))

    message = msg.MSG_ORDER_CREATED.format(
        raffle_title=order.raffle.title,
        numbers=numbers_str,
        qty=order.qty,
        currency=order.raffle.currency,
        total=order.total_amount,
        timeout=settings.RESERVATION_TIMEOUT_MINUTES
    )

    send_text(contact.wa_id, message)
    contact.update_state(ContactState.CONFIRMING_ORDER, {'order_id': order.id})


def handle_confirming_order(contact, text):
    """Handle order confirmation."""
    text_lower = text.lower()

    if text_lower in ['cancelar', 'cancel']:
        order_id = contact.context.get('order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                release_order_reservations(order)
                send_text(contact.wa_id, msg.MSG_ORDER_CANCELLED)
            except Exception as e:
                logger.error(f"Error cancelling order: {e}")
                send_text(contact.wa_id, msg.MSG_ORDER_CANCELLED)

        contact.update_state(ContactState.IDLE)
        contact.clear_context()
        show_main_menu(contact)
        return

    if text_lower in ['confirmar', 'confirm']:
        order_id = contact.context.get('order_id')
        if not order_id:
            send_text(contact.wa_id, msg.MSG_SESSION_EXPIRED)
            contact.update_state(ContactState.IDLE)
            return

        try:
            order = Order.objects.get(id=order_id, contact=contact)
            send_payment_instructions(contact, order)
        except Order.DoesNotExist:
            send_text(contact.wa_id, msg.MSG_SESSION_EXPIRED)
            contact.update_state(ContactState.IDLE)
        return

    send_text(contact.wa_id, msg.MSG_CONFIRM_OR_CANCEL)


def send_payment_instructions(contact, order):
    """Send payment instructions to contact."""
    message = msg.MSG_PAYMENT_INSTRUCTIONS.format(
        currency=order.raffle.currency,
        amount=order.total_amount,
        order_id=order.id
    )

    send_text(contact.wa_id, message)
    contact.update_state(ContactState.UPLOADING_PROOF, {'order_id': order.id})


def handle_awaiting_payment(contact, text):
    """Handle messages while awaiting payment."""
    send_text(contact.wa_id, msg.MSG_CHECK_ORDER_STATUS)


def handle_uploading_proof(contact, inbound_message):
    """Handle payment proof upload."""
    order_id = contact.context.get('order_id')

    if not order_id:
        send_text(contact.wa_id, msg.MSG_SESSION_EXPIRED)
        contact.update_state(ContactState.IDLE)
        return

    # Check if image/document received
    if inbound_message.media_id:
        try:
            order = Order.objects.get(id=order_id, contact=contact)
            order.payment_proof_media_id = inbound_message.media_id
            order.save(update_fields=['payment_proof_media_id', 'updated_at'])

            send_text(contact.wa_id, msg.MSG_PAYMENT_PROOF_RECEIVED)
            contact.update_state(ContactState.IDLE)
            contact.clear_context()

        except Order.DoesNotExist:
            send_text(contact.wa_id, msg.MSG_SESSION_EXPIRED)
            contact.update_state(ContactState.IDLE)

    else:
        text = (inbound_message.text or '').strip().lower()
        if text in ['saltar', 'skip']:
            send_text(contact.wa_id, msg.MSG_PAYMENT_SKIPPED)
            contact.update_state(ContactState.IDLE)
            contact.clear_context()
        else:
            send_text(contact.wa_id, msg.MSG_PAYMENT_PROOF_REQUEST)


def parse_numbers(text):
    """
    Parse ticket numbers from text input.
    Accepts formats: "12,13,99" or "12 13 99"

    Returns:
        List of integers or None if invalid
    """
    # Replace commas with spaces and split
    text = text.replace(',', ' ')
    parts = text.split()

    try:
        numbers = [int(p.strip()) for p in parts if p.strip()]
        return numbers if numbers else None
    except ValueError:
        return None
