from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
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
        (_('Información Básica'), {
            'fields': ('title', 'description', 'is_active')
        }),
        (_('Precio'), {
            'fields': ('ticket_price', 'currency')
        }),
        (_('Rango de Números'), {
            'fields': ('min_number', 'max_number')
        }),
        (_('Información del Sorteo'), {
            'fields': ('draw_date', 'winner_number'),
            'classes': ('collapse',)
        }),
        (_('Fechas'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_raffles', 'deactivate_raffles', 'generate_tickets']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.display(description=_('Estado'))
    def is_active_badge(self, obj):
        if obj.is_active:
            return mark_safe(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Activo</span>'
            )
        return mark_safe(
            '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">Inactivo</span>'
        )

    @admin.display(description=_('Rango de Números'))
    def range_display(self, obj):
        return f"{obj.min_number} - {obj.max_number} ({obj.total_tickets} total)"

    @admin.display(description=_('Disponibilidad'))
    def availability_display(self, obj):
        available = obj.available_count
        sold = obj.sold_count
        total = obj.total_tickets
        percent_sold = (sold / total * 100) if total > 0 else 0

        return format_html(
            '<span title="Disponibles: {} | Vendidos: {} | Total: {}">'
            '✅ {} | 🔥 {} ({}%)'
            '</span>',
            available, sold, total,
            available, sold, f"{percent_sold:.1f}"
        )

    @admin.action(description=_("Activar rifas seleccionadas"))
    def activate_raffles(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} rifa(s) activada(s).")

    @admin.action(description=_("Desactivar rifas seleccionadas"))
    def deactivate_raffles(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} rifa(s) desactivada(s).")

    @admin.action(description=_("Generar boletos para rifas seleccionadas"))
    def generate_tickets(self, request, queryset):
        """Generate ticket numbers for selected raffles."""
        total_created = 0
        for raffle in queryset:
            existing_count = TicketNumber.objects.filter(raffle=raffle).count()
            if existing_count > 0:
                self.message_user(
                    request,
                    f"La rifa '{raffle.title}' ya tiene boletos.",
                    level='warning'
                )
                continue

            tickets = [
                TicketNumber(raffle=raffle, number=num)
                for num in range(raffle.min_number, raffle.max_number + 1)
            ]
            TicketNumber.objects.bulk_create(tickets)
            total_created += len(tickets)

        self.message_user(request, f"{total_created} boleto(s) generado(s).")


@admin.register(TicketNumber)
class TicketNumberAdmin(admin.ModelAdmin):
    list_display = ['raffle', 'number', 'status_badge', 'reserved_by_order', 'reserved_until']
    list_filter = ['status', 'raffle', 'reserved_until']
    search_fields = ['number', 'raffle__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['raffle', 'number']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    fieldsets = (
        (_('Información del Boleto'), {
            'fields': ('raffle', 'number', 'status')
        }),
        (_('Reserva'), {
            'fields': ('reserved_by_order', 'reserved_until')
        }),
        (_('Fechas'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Estado'))
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


class OrderTicketInline(admin.TabularInline):
    model = OrderTicket
    extra = 0
    can_delete = False

    def get_fields(self, request, obj=None):
        if obj:  # Editing existing order
            return ['ticket', 'ticket_number', 'ticket_status']
        return ['ticket']  # Adding new order

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['ticket_number', 'ticket_status']
        return []

    @admin.display(description=_('Número'))
    def ticket_number(self, obj):
        if obj and obj.pk:
            return obj.ticket.number
        return '-'

    @admin.display(description=_('Estado'))
    def ticket_status(self, obj):
        if obj and obj.pk:
            return obj.ticket.get_status_display()
        return '-'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'raffle_title',
        'contact_name',
        'qty',
        'total_amount',
        'status_badge',
        'ticket_numbers_display',
        'created_at',
        'expires_at',
    ]
    list_filter = ['status', 'raffle', 'created_at', 'paid_at']
    search_fields = ['id', 'contact__wa_id', 'contact__name', 'raffle__title']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [OrderTicketInline]
    autocomplete_fields = ['raffle', 'contact']

    def get_readonly_fields(self, request, obj=None):
        """
        Operators (non-superusers) can only change status.
        Admins (superusers) have full access.
        """
        if request.user.is_superuser:
            # Superuser: minimal readonly
            if obj:
                return ['created_at', 'updated_at', 'paid_at', 'total_amount']
            return ['created_at', 'updated_at', 'paid_at']
        else:
            # Operator: can only change status field
            if obj:
                return [
                    'raffle', 'contact', 'qty', 'total_amount',
                    'payment_proof_media_id', 'created_at', 'updated_at', 
                    'paid_at', 'expires_at'
                ]
            # Operators cannot add new orders
            return ['raffle', 'contact', 'qty', 'total_amount', 'status',
                    'payment_proof_media_id', 'created_at', 'updated_at', 
                    'paid_at', 'expires_at']

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            # Full access for superusers
            if obj:
                return (
                    (_('Información de la Orden'), {
                        'fields': ('raffle', 'contact', 'qty', 'total_amount', 'status')
                    }),
                    (_('Pago'), {
                        'fields': ('payment_proof_media_id', 'paid_at')
                    }),
                    (_('Fechas'), {
                        'fields': ('created_at', 'updated_at', 'expires_at'),
                        'classes': ('collapse',)
                    }),
                )
            return (
                (_('Información de la Orden'), {
                    'fields': ('raffle', 'contact', 'qty', 'status')
                }),
                (_('Opcional'), {
                    'fields': ('expires_at',),
                    'classes': ('collapse',)
                }),
            )
        else:
            # Operators: simplified view, can only change status
            if obj:
                return (
                    (_('Información de la Orden (Solo Lectura)'), {
                        'fields': ('raffle', 'contact', 'qty', 'total_amount'),
                        'description': _('Solo puedes cambiar el estado de la orden.')
                    }),
                    (_('Cambiar Estado'), {
                        'fields': ('status',),
                        'description': _('Selecciona PAGADO para confirmar el pago. Se enviará notificación automática al cliente.')
                    }),
                )
            return (
                (_('Sin permisos'), {
                    'fields': (),
                    'description': _('No tienes permisos para crear órdenes.')
                }),
            )

    def has_add_permission(self, request):
        """Only superusers can add orders."""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete orders."""
        return request.user.is_superuser

    @admin.display(description=_('Rifa'), ordering='raffle__title')
    def raffle_title(self, obj):
        return obj.raffle.title if obj.raffle else '-'

    @admin.display(description=_('Contacto'), ordering='contact__name')
    def contact_name(self, obj):
        if obj.contact:
            return obj.contact.name or obj.contact.wa_id
        return '-'

    actions = ['confirm_payment_action', 'cancel_order_action']

    @admin.display(description=_('Estado'))
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

    @admin.display(description=_('Boletos'))
    def ticket_numbers_display(self, obj):
        numbers = obj.ticket_numbers
        if len(numbers) <= 5:
            return ', '.join(map(str, numbers))
        return f"{', '.join(map(str, numbers[:5]))}... (+{len(numbers)-5} más)"

    @admin.action(description=_("Confirmar pago de órdenes seleccionadas"))
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
                    f"Orden {order.id}: {str(e)}",
                    level='error'
                )
                error_count += 1

        if success_count:
            self.message_user(request, f"{success_count} orden(es) confirmada(s).")
        if error_count:
            self.message_user(
                request,
                f"{error_count} orden(es) no pudieron ser confirmadas.",
                level='warning'
            )

    @admin.action(description=_("Cancelar órdenes seleccionadas"))
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
                    f"Orden {order.id}: {str(e)}",
                    level='error'
                )
                error_count += 1

        if success_count:
            self.message_user(
                request,
                f"{success_count} orden(es) cancelada(s), {total_released} boleto(s) liberado(s)."
            )
        if error_count:
            self.message_user(
                request,
                f"{error_count} orden(es) no pudieron ser canceladas.",
                level='warning'
            )


@admin.register(OrderTicket)
class OrderTicketAdmin(admin.ModelAdmin):
    list_display = ['order', 'ticket', 'ticket_number', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order__id', 'ticket__number']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    @admin.display(description=_('Número de Boleto'))
    def ticket_number(self, obj):
        return obj.ticket.number
