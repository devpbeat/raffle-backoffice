import hashlib
import hmac
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def verify_meta_signature(payload, signature):
    """
    Verify the signature from Meta's webhook request.

    Args:
        payload: Raw request body as bytes
        signature: X-Hub-Signature-256 header value

    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not signature:
        logger.warning("No signature provided in webhook request")
        return False

    if not settings.WHATSAPP_APP_SECRET:
        logger.warning("WHATSAPP_APP_SECRET not configured, skipping verification")
        return True  # Allow in development if secret not set

    try:
        # Signature format: sha256=<signature>
        expected_signature = signature.split('=')[1] if '=' in signature else signature

        # Calculate expected signature
        mac = hmac.new(
            settings.WHATSAPP_APP_SECRET.encode('utf-8'),
            msg=payload,
            digestmod=hashlib.sha256
        )
        calculated_signature = mac.hexdigest()

        # Compare signatures
        is_valid = hmac.compare_digest(calculated_signature, expected_signature)

        if not is_valid:
            logger.warning("Invalid webhook signature")

        return is_valid

    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False
