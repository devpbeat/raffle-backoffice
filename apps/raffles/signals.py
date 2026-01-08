from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
import logging

from apps.raffles.models import Order, OrderStatus, TicketNumber, TicketStatus

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    """Track the previous status before saving."""
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except Order.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    """
    Handle order status changes:
    - When order is marked as PAID: update tickets to SOLD and send WhatsApp notification
    - When order is CANCELLED: release tickets back to AVAILABLE
    """
    previous_status = getattr(instance, '_previous_status', None)
    
    # Skip if this is a new order or status didn't change
    if created or not previous_status or previous_status == instance.status:
        return
    
    # ========== PAID: Mark tickets as SOLD + Send notification ==========
    if instance.status == OrderStatus.PAID and previous_status != OrderStatus.PAID:
        logger.info(f"Order #{instance.id} marked as PAID (was {previous_status})")
        
        # Update tickets to SOLD
        with transaction.atomic():
            tickets_updated = TicketNumber.objects.filter(
                reserved_by_order=instance
            ).update(
                status=TicketStatus.SOLD,
                reserved_until=None
            )
            
            # If no tickets were reserved, try to find tickets through OrderTicket
            if tickets_updated == 0:
                from apps.raffles.models import OrderTicket
                ticket_ids = OrderTicket.objects.filter(order=instance).values_list('ticket_id', flat=True)
                if ticket_ids:
                    tickets_updated = TicketNumber.objects.filter(id__in=ticket_ids).update(
                        status=TicketStatus.SOLD,
                        reserved_by_order=instance,
                        reserved_until=None
                    )
            
            # Update paid_at if not set
            if not instance.paid_at:
                Order.objects.filter(pk=instance.pk).update(paid_at=timezone.now())
            
            logger.info(f"Marked {tickets_updated} ticket(s) as SOLD for Order #{instance.id}")
        
        # Send WhatsApp notification
        try:
            from apps.whatsapp.services.meta_client import send_payment_confirmation
            send_payment_confirmation(instance)
            logger.info(f"WhatsApp notification sent to {instance.contact.wa_id}")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp notification for Order #{instance.id}: {e}")
    
    # ========== CANCELLED: Release tickets back to AVAILABLE ==========
    elif instance.status == OrderStatus.CANCELLED and previous_status != OrderStatus.CANCELLED:
        logger.info(f"Order #{instance.id} CANCELLED (was {previous_status})")
        
        with transaction.atomic():
            tickets_released = TicketNumber.objects.filter(
                reserved_by_order=instance
            ).update(
                status=TicketStatus.AVAILABLE,
                reserved_by_order=None,
                reserved_until=None
            )
            logger.info(f"Released {tickets_released} ticket(s) for Order #{instance.id}")
    
    # ========== EXPIRED: Release tickets back to AVAILABLE ==========
    elif instance.status == OrderStatus.EXPIRED and previous_status != OrderStatus.EXPIRED:
        logger.info(f"Order #{instance.id} EXPIRED (was {previous_status})")
        
        with transaction.atomic():
            tickets_released = TicketNumber.objects.filter(
                reserved_by_order=instance
            ).update(
                status=TicketStatus.AVAILABLE,
                reserved_by_order=None,
                reserved_until=None
            )
            logger.info(f"Released {tickets_released} ticket(s) for Order #{instance.id}")
