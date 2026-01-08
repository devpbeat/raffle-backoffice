import uuid
from decimal import Decimal


class BancardMockClient:
    """
    Mock implementation of Bancard payment gateway.

    For production, this should be replaced with the actual Bancard API integration.
    This mock simulates the basic flow: create payment request, check status, process webhooks.
    """

    def __init__(self, merchant_id, api_key):
        """
        Initialize Bancard client with credentials.

        Args:
            merchant_id (str): Merchant ID from Bancard
            api_key (str): API key from Bancard
        """
        self.merchant_id = merchant_id
        self.api_key = api_key

    def create_payment_request(self, amount, currency, order_id, description):
        """
        Create a payment request with Bancard.

        In a real implementation, this would call Bancard's API to create
        a payment request and return a checkout URL for the customer.

        Args:
            amount (Decimal): Payment amount
            currency (str): Currency code (e.g., 'PYG', 'USD')
            order_id (str): Internal order/appointment ID
            description (str): Payment description

        Returns:
            dict: {
                'transaction_id': str,
                'payment_url': str,
                'status': str,
                'amount': str,
                'currency': str,
                'order_id': str
            }
        """
        # Generate mock transaction ID
        transaction_id = f"BANCARD-MOCK-{uuid.uuid4().hex[:12].upper()}"

        # Mock response
        response = {
            'transaction_id': transaction_id,
            'payment_url': f"https://mock.bancard.com.py/checkout/{transaction_id}",
            'status': 'pending',
            'amount': str(amount),
            'currency': currency,
            'order_id': order_id,
            'description': description,
        }

        return response

    def check_payment_status(self, transaction_id):
        """
        Check the status of a payment transaction.

        In a real implementation, this would query Bancard's API
        to get the current status of a transaction.

        Args:
            transaction_id (str): Transaction ID to check

        Returns:
            dict: {
                'transaction_id': str,
                'status': str,  # 'pending', 'paid', 'failed', 'refunded'
                'paid_at': str (ISO datetime),
                'amount': str,
                'currency': str
            }
        """
        # Mock: For testing, we'll assume all transactions are paid
        # In reality, you'd query the actual status from Bancard
        return {
            'transaction_id': transaction_id,
            'status': 'paid',  # Mock always returns 'paid'
            'paid_at': '2026-01-08T12:00:00Z',
            'amount': '0.00',
            'currency': 'USD'
        }

    def process_webhook(self, payload, signature):
        """
        Process an incoming webhook from Bancard.

        In a real implementation, you would:
        1. Verify the signature to ensure the webhook is from Bancard
        2. Process the payment confirmation
        3. Update your database accordingly

        Args:
            payload (dict): Webhook payload from Bancard
            signature (str): Signature header for verification

        Returns:
            dict: {
                'transaction_id': str,
                'status': str,
                'amount': Decimal,
                'currency': str,
                'verified': bool
            }
        """
        # Mock signature verification
        # In reality, verify using Bancard's signature mechanism (HMAC, etc.)
        verified = True  # Mock always verifies

        # Extract data from payload
        result = {
            'transaction_id': payload.get('transaction_id'),
            'status': payload.get('status', 'paid'),
            'amount': Decimal(payload.get('amount', '0.00')),
            'currency': payload.get('currency', 'USD'),
            'verified': verified,
            'raw_payload': payload
        }

        return result

    def refund_payment(self, transaction_id, amount=None):
        """
        Initiate a refund for a payment.

        Args:
            transaction_id (str): Transaction ID to refund
            amount (Decimal, optional): Partial refund amount. If None, full refund.

        Returns:
            dict: {
                'refund_id': str,
                'status': str,
                'amount_refunded': str
            }
        """
        # Generate mock refund ID
        refund_id = f"REFUND-{uuid.uuid4().hex[:12].upper()}"

        return {
            'refund_id': refund_id,
            'transaction_id': transaction_id,
            'status': 'refunded',
            'amount_refunded': str(amount) if amount else 'full'
        }


def get_bancard_client(tenant):
    """
    Get a configured Bancard client for a specific tenant.

    Retrieves the tenant's Bancard integration configuration and
    returns an initialized client.

    Args:
        tenant (Tenant): Tenant instance

    Returns:
        BancardMockClient or None: Configured client, or None if not configured

    Raises:
        TenantIntegration.DoesNotExist: If Bancard is not configured for this tenant
    """
    try:
        from apps.integrations.models import TenantIntegration, IntegrationType

        integration = TenantIntegration.objects.get(
            tenant=tenant,
            integration_type=IntegrationType.BANCARD,
            is_active=True
        )

        config = integration.config
        return BancardMockClient(
            merchant_id=config.get('merchant_id'),
            api_key=config.get('api_key')
        )

    except Exception:
        # Integrations app might not be created yet, or tenant not configured
        # Return a default mock client for testing
        return BancardMockClient(
            merchant_id='MOCK_MERCHANT',
            api_key='MOCK_API_KEY'
        )


def create_payment_for_order(order):
    """
    Create a Bancard payment request for an Order.

    Args:
        order (Order): Order instance from raffles app

    Returns:
        dict: Payment request response from Bancard
    """
    client = get_bancard_client(order.tenant)

    return client.create_payment_request(
        amount=order.total_amount,
        currency=order.raffle.currency,
        order_id=str(order.id),
        description=f"Rifa: {order.raffle.title} - {order.qty} boleto(s)"
    )


def create_payment_for_appointment(appointment):
    """
    Create a Bancard payment request for an Appointment.

    Args:
        appointment (Appointment): Appointment instance

    Returns:
        dict: Payment request response from Bancard
    """
    client = get_bancard_client(appointment.tenant)

    return client.create_payment_request(
        amount=appointment.total_amount,
        currency=appointment.currency,
        order_id=str(appointment.id),
        description=f"Cita: {appointment.service.name} - {appointment.customer.name}"
    )
