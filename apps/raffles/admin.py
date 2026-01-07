from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from apps.raffles.models import Raffle, TicketNumber, Order, OrderTicket
from apps.raffles.services import confirm_paid, release_order_reservations, ReservationError


class TicketNumberInline(admin.TabularInline):
    model = TicketNumber
    extra = 0
    fields = ['number', 'status', 'reserved_by_order', 'reserved_until']
    readonly_fields = ['reserved_by_order', 'reserved_until']
    can_delete = False


@admin.register(Raffle)
class RaffleAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'ticket_price',
        'currency',
        'is_active_badge',
        'range_display',
        'availability_display',
        'created_at',
    ]
    list_filter = ['is_active', 'currency', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('ticket_price', 'currency')
        }),
        ('Ticket Range', {
            'fields': ('min_number', 'max_number')
        }),
        ('Draw Information', {
            'fields': ('draw_date', 'winner_number'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_raffles', 'deactivate_raffles', 'generate_tickets']

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    is_active_badge.short_description = 'Status'

    def range_display(self, obj):
        return f"{obj.min_number} - {obj.max_number} ({obj.total_tickets} total)"
    range_display.short_description = 'Number Range'

    def availability_display(self, obj):
        available = obj.available_count
        sold = obj.sold_count
        total = obj.total_tickets
        percent_sold = (sold / total * 100) if total > 0 else 0

        return format_html(
            '<span title="Available: {} | Sold: {} | Total: {}">'
            '✅ {} | 🔥 {} ({:.1f}%)'
            '</span>',
            available, sold, total,
            available, sold, percent_sold
        )
    availability_display.short_description = 'Availability'

    def activate_raffles(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} raffle(s) activated.")
    activate_raffles.short_description = "Activate selected raffles"

    def deactivate_raffles(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} raffle(s) deactivated.")
    deactivate_raffles.short_description = "Deactivate selected raffles"

    def generate_tickets(self, request, queryset):
        """Generate ticket numbers for selected raffles."""
        total_created = 0
        for raffle in queryset:
            existing_count = TicketNumber.objects.filter(raffle=raffle).count()
            if existing_count > 0:
                self.message_user(
                    request,
                    f"Raffle '{raffle.title}' already has tickets.",
                    level='warning'
                )
                continue

            tickets = [
                TicketNumber(raffle=raffle, number=num)
                for num in range(raffle.min_number, raffle.max_number + 1)
            ]
            TicketNumber.objects.bulk_create(tickets)
            total_created += len(tickets)

        self.message_user(request, f"{total_created} ticket(s) generated.")
    generate_tickets.short_description = "Generate tickets for selected raffles"


@admin.register(TicketNumber)
class TicketNumberAdmin(admin.ModelAdmin):
    list_display = ['raffle', 'number', 'status_badge', 'reserved_by_order', 'reserved_until']
    list_filter = ['status', 'raffle', 'reserved_until']
    search_fields = ['number', 'raffle__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['raffle', 'number']

    fieldsets = (
        ('Ticket Information', {
            'fields': ('raffle', 'number', 'status')
        }),
        ('Reservation', {
            'fields': ('reserved_by_order', 'reserved_until')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'AVAILABLE': 'green',
            'RESERVED': 'orange',
            'SOLD': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


class OrderTicketInline(admin.TabularInline):
    model = OrderTicket
    extra = 0
    fields = ['ticket', 'ticket_number', 'ticket_status']
    readonly_fields = ['ticket_number', 'ticket_status']
    can_delete = False

    def ticket_number(self, obj):
        return obj.ticket.number
    ticket_number.short_description = 'Number'

    def ticket_status(self, obj):
        return obj.ticket.get_status_display()
    ticket_status.short_description = 'Status'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'raffle_link',
        'contact_link',
        'qty',
        'total_amount',
        'status_badge',
        'ticket_numbers_display',
        'created_at',
        'expires_at',
    ]
    list_filter = ['status', 'raffle', 'created_at', 'paid_at']
    search_fields = ['id', 'contact__wa_id', 'contact__name', 'raffle__title']
    readonly_fields = ['created_at', 'updated_at', 'paid_at', 'total_amount']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [OrderTicketInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('raffle', 'contact', 'qty', 'total_amount', 'status')
        }),
        ('Payment', {
            'fields': ('payment_proof_media_id', 'paid_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['confirm_payment_action', 'cancel_order_action']

    def raffle_link(self, obj):
        return format_html(
            '<a href="/admin/raffles/raffle/{}/change/">{}</a>',
            obj.raffle.id,
            obj.raffle.title
        )
    raffle_link.short_description = 'Raffle'

    def contact_link(self, obj):
        return format_html(
            '<a href="/admin/whatsapp/whatsappcontact/{}/change/">{}</a>',
            obj.contact.id,
            obj.contact.name or obj.contact.wa_id
        )
    contact_link.short_description = 'Contact'

    def status_badge(self, obj):
        colors = {
            'DRAFT': 'gray',
            'PENDING_PAYMENT': 'orange',
            'PAID': 'green',
            'CANCELLED': 'red',
            'EXPIRED': 'darkred',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def ticket_numbers_display(self, obj):
        numbers = obj.ticket_numbers
        if len(numbers) <= 5:
            return ', '.join(map(str, numbers))
        return f"{', '.join(map(str, numbers[:5]))}... (+{len(numbers)-5} more)"
    ticket_numbers_display.short_description = 'Tickets'

    def confirm_payment_action(self, request, queryset):
        """Admin action to confirm payment for selected orders."""
        success_count = 0
        error_count = 0

        for order in queryset:
            try:
                confirm_paid(order)
                success_count += 1
            except ReservationError as e:
                self.message_user(
                    request,
                    f"Order {order.id}: {str(e)}",
                    level='error'
                )
                error_count += 1

        if success_count:
            self.message_user(request, f"{success_count} order(s) confirmed.")
        if error_count:
            self.message_user(
                request,
                f"{error_count} order(s) could not be confirmed.",
                level='warning'
            )
    confirm_payment_action.short_description = "Confirm payment for selected orders"

    def cancel_order_action(self, request, queryset):
        """Admin action to cancel selected orders."""
        success_count = 0
        error_count = 0
        total_released = 0

        for order in queryset:
            try:
                released = release_order_reservations(order)
                total_released += released
                success_count += 1
            except ReservationError as e:
                self.message_user(
                    request,
                    f"Order {order.id}: {str(e)}",
                    level='error'
                )
                error_count += 1

        if success_count:
            self.message_user(
                request,
                f"{success_count} order(s) cancelled, {total_released} ticket(s) released."
            )
        if error_count:
            self.message_user(
                request,
                f"{error_count} order(s) could not be cancelled.",
                level='warning'
            )
    cancel_order_action.short_description = "Cancel selected orders"


@admin.register(OrderTicket)
class OrderTicketAdmin(admin.ModelAdmin):
    list_display = ['order', 'ticket', 'ticket_number', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order__id', 'ticket__number']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def ticket_number(self, obj):
        return obj.ticket.number
    ticket_number.short_description = 'Ticket Number'
