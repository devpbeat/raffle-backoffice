import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db import IntegrityError
from apps.whatsapp.models import WhatsAppContact, InboundMessage, MessageType
from apps.whatsapp.services import verify_meta_signature, process_message

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def webhook_verify(request):
    """
    Webhook verification endpoint for Meta WhatsApp Cloud API.
    Meta will send a GET request with verification token.
    """
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')

    if mode == 'subscribe' and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return HttpResponse(challenge, content_type='text/plain')

    logger.warning(f"Webhook verification failed: mode={mode}, token_match={token == settings.WHATSAPP_VERIFY_TOKEN}")
    return HttpResponse('Verification failed', status=403)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_receive(request):
    """
    Webhook endpoint for receiving WhatsApp messages.
    Validates signature, parses messages, and processes them.
    """
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not verify_meta_signature(request.body, signature):
        logger.warning("Invalid webhook signature")
        return JsonResponse({'error': 'Invalid signature'}, status=403)

    try:
        payload = json.loads(request.body)
        logger.info(f"Received webhook payload: {json.dumps(payload, indent=2)}")

        # Process each entry in the payload
        for entry in payload.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})

                # Process messages
                for message in value.get('messages', []):
                    process_inbound_message(message, value)

                # Process status updates (optional logging)
                for status in value.get('statuses', []):
                    logger.info(f"Message status update: {status}")

        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


def process_inbound_message(message, value):
    """
    Process a single inbound message from the webhook payload.

    Args:
        message: Message dict from webhook payload
        value: Value dict containing metadata
    """
    wa_message_id = message.get('id')
    from_wa_id = message.get('from')
    msg_type = message.get('type', 'unknown')
    timestamp = message.get('timestamp')

    if not wa_message_id or not from_wa_id:
        logger.warning(f"Invalid message structure: {message}")
        return

    # Get or create contact
    contact, created = WhatsAppContact.objects.get_or_create(
        wa_id=from_wa_id,
        defaults={'name': value.get('contacts', [{}])[0].get('profile', {}).get('name')}
    )

    if created:
        logger.info(f"New contact created: {contact.wa_id}")

    # Extract message content based on type
    text = None
    media_id = None

    if msg_type == 'text':
        text = message.get('text', {}).get('body', '')
    elif msg_type == 'image':
        media_id = message.get('image', {}).get('id')
        text = message.get('image', {}).get('caption', '')
    elif msg_type == 'document':
        media_id = message.get('document', {}).get('id')
        text = message.get('document', {}).get('caption', '')
    elif msg_type == 'audio':
        media_id = message.get('audio', {}).get('id')
    elif msg_type == 'video':
        media_id = message.get('video', {}).get('id')
        text = message.get('video', {}).get('caption', '')
    elif msg_type == 'interactive':
        interactive = message.get('interactive', {})
        button_reply = interactive.get('button_reply', {})
        list_reply = interactive.get('list_reply', {})
        text = button_reply.get('title') or list_reply.get('title') or ''

    # Map message type to enum
    msg_type_enum = {
        'text': MessageType.TEXT,
        'image': MessageType.IMAGE,
        'document': MessageType.DOCUMENT,
        'audio': MessageType.AUDIO,
        'video': MessageType.VIDEO,
        'sticker': MessageType.STICKER,
        'location': MessageType.LOCATION,
        'contacts': MessageType.CONTACTS,
        'interactive': MessageType.INTERACTIVE,
        'button': MessageType.BUTTON,
    }.get(msg_type, MessageType.UNKNOWN)

    # Create inbound message (with deduplication)
    try:
        inbound_message = InboundMessage.objects.create(
            wa_message_id=wa_message_id,
            contact=contact,
            msg_type=msg_type_enum,
            text=text,
            media_id=media_id,
            raw_payload=message,
        )

        logger.info(f"Created inbound message: {inbound_message}")

        # Process the message through the flow
        process_message(inbound_message)

    except IntegrityError:
        logger.info(f"Duplicate message ignored: {wa_message_id}")
    except Exception as e:
        logger.error(f"Error creating/processing inbound message: {e}", exc_info=True)
