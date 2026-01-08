from django.contrib import admin
from django.contrib.admin.apps import AdminConfig
from django.db.models import Sum
from decimal import Decimal


class RaffleAdminSite(admin.AdminSite):
    site_header = 'Admin Rifas'
    site_title = 'Administración de Rifas'
    index_title = 'Panel de Control'

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Get dashboard stats
        dashboard_stats = self._get_dashboard_stats()
        extra_context['dashboard_stats'] = dashboard_stats
        
        return super().index(request, extra_context=extra_context)

    def _get_dashboard_stats(self):
        """Calculate dashboard statistics for active raffle."""
        from apps.raffles.models import Raffle, Order, OrderStatus
        
        # Get the first active raffle
        active_raffle = Raffle.objects.filter(is_active=True).first()
        
        if not active_raffle:
            return {'active_raffle': None}
        
        # Ticket counts
        total_tickets = active_raffle.total_tickets
        available_tickets = active_raffle.available_count
        reserved_tickets = active_raffle.reserved_count
        sold_tickets = active_raffle.sold_count
        
        # Calculate percentages
        sold_percent = round((sold_tickets / total_tickets * 100), 1) if total_tickets > 0 else 0
        reserved_percent = round((reserved_tickets / total_tickets * 100), 1) if total_tickets > 0 else 0
        
        # Order counts
        orders = Order.objects.filter(raffle=active_raffle)
        orders_draft = orders.filter(status=OrderStatus.DRAFT).count()
        orders_pending = orders.filter(status=OrderStatus.PENDING_PAYMENT).count()
        orders_paid = orders.filter(status=OrderStatus.PAID).count()
        orders_cancelled = orders.filter(status=OrderStatus.CANCELLED).count()
        orders_expired = orders.filter(status=OrderStatus.EXPIRED).count()
        
        # Revenue calculation
        paid_orders = orders.filter(status=OrderStatus.PAID)
        total_revenue = paid_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        return {
            'active_raffle': active_raffle,
            'total_tickets': total_tickets,
            'available_tickets': available_tickets,
            'reserved_tickets': reserved_tickets,
            'sold_tickets': sold_tickets,
            'sold_percent': sold_percent,
            'reserved_percent': reserved_percent,
            'orders_draft': orders_draft,
            'orders_pending': orders_pending,
            'orders_paid': orders_paid,
            'orders_cancelled': orders_cancelled,
            'orders_expired': orders_expired,
            'total_revenue': total_revenue,
            'currency': active_raffle.currency,
            'ticket_price': active_raffle.ticket_price,
        }


class RaffleAdminConfig(AdminConfig):
    default_site = 'core.admin.RaffleAdminSite'
