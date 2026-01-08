import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppAPIError(Exception):
    pass


def _get_api_url():
    return f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"


def _get_headers():
    return {
        'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}',
        'Content-Type': 'application/json',
    }


def send_message(payload):
    """
    Send a message via WhatsApp Cloud API.

    Args:
        payload: Dictionary with message payload

    Returns:
        Response JSON from WhatsApp API

    Raises:
        WhatsAppAPIError: If the API request fails
    """
    try:
        response = requests.post(
            _get_api_url(),
            headers=_get_headers(),
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp API error: {e}")
        raise WhatsAppAPIError(f"Failed to send message: {e}")


def send_text(to, message):
    """
    Send a text message to a WhatsApp number.

    Args:
        to: WhatsApp ID (phone number)
        message: Text message to send

    Returns:
        Response JSON from WhatsApp API
    """
    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': to,
        'type': 'text',
        'text': {
            'preview_url': False,
            'body': message
        }
    }
    return send_message(payload)


def send_interactive_buttons(to, body_text, buttons):
    """
    Send an interactive message with buttons.

    Args:
        to: WhatsApp ID
        body_text: Message body text
        buttons: List of button dicts with 'id' and 'title' keys (max 3)

    Returns:
        Response JSON from WhatsApp API
    """
    if len(buttons) > 3:
        raise WhatsAppAPIError("Maximum 3 buttons allowed")

    button_components = [
        {
            'type': 'reply',
            'reply': {
                'id': btn['id'],
                'title': btn['title'][:20]  # Max 20 chars
            }
        }
        for btn in buttons
    ]

    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': to,
        'type': 'interactive',
        'interactive': {
            'type': 'button',
            'body': {
                'text': body_text
            },
            'action': {
                'buttons': button_components
            }
        }
    }
    return send_message(payload)


def send_interactive_list(to, body_text, button_text, sections):
    """
    Send an interactive list message.

    Args:
        to: WhatsApp ID
        body_text: Message body text
        button_text: Text for the button (e.g., "View Options")
        sections: List of section dicts with 'title' and 'rows' keys

    Returns:
        Response JSON from WhatsApp API
    """
    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': to,
        'type': 'interactive',
        'interactive': {
            'type': 'list',
            'body': {
                'text': body_text
            },
            'action': {
                'button': button_text[:20],
                'sections': sections
            }
        }
    }
    return send_message(payload)


def send_payment_confirmation(order):
    """
    Send payment confirmation message to customer via WhatsApp.

    Args:
        order: Order instance that was just paid

    Returns:
        Response JSON from WhatsApp API or None if failed
    """
    from apps.whatsapp.services.messages_es import MSG_PAYMENT_CONFIRMED
    
    contact = order.contact
    raffle = order.raffle
    
    # Format ticket numbers
    numbers = order.ticket_numbers
    if len(numbers) <= 10:
        numbers_str = ', '.join(map(str, numbers))
    else:
        numbers_str = f"{', '.join(map(str, numbers[:10]))}... (+{len(numbers)-10} más)"
    
    # Build the confirmation message
    message = MSG_PAYMENT_CONFIRMED.format(
        name=contact.name or 'Cliente',
        raffle_title=raffle.title,
        numbers=numbers_str,
        qty=order.qty,
        currency=raffle.currency,
        total=order.total_amount,
    )
    
    try:
        result = send_text(contact.wa_id, message)
        logger.info(f"Payment confirmation sent to {contact.wa_id} for Order #{order.id}")
        return result
    except WhatsAppAPIError as e:
        logger.error(f"Failed to send payment confirmation to {contact.wa_id}: {e}")
        return None
