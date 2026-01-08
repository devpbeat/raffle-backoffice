from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from apps.appointments.models import Service, Customer, Appointment, AppointmentStatus
from apps.appointments.services.bookings import (
    confirm_appointment,
    cancel_appointment,
    complete_appointment,
    mark_no_show,
    BookingError,
)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'tenant',
        'duration_minutes',
        'price_display',
        'is_active_badge',
        'max_bookings_per_day',
        'created_at',
    ]
    list_filter = ['tenant', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (_('Información del Servicio'), {
            'fields': ('tenant', 'name', 'description', 'is_active')
        }),
        (_('Precio'), {
            'fields': ('price', 'currency')
        }),
        (_('Duración y Buffer'), {
            'fields': ('duration_minutes', 'buffer_time_minutes')
        }),
        (_('Límites de Reserva'), {
            'fields': ('max_bookings_per_day', 'advance_booking_days')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        """Format price with currency."""
        return f"{obj.currency} {obj.price}"
    price_display.short_description = _('Precio')

    def is_active_badge(self, obj):
        """Display active status as colored badge."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">✓ Activo</span>'
            )
        else:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">✗ Inactivo</span>'
            )
    is_active_badge.short_description = _('Estado')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'tenant',
        'phone',
        'email',
        'total_appointments_display',
        'last_appointment_at',
        'created_at',
    ]
    list_filter = ['tenant', 'created_at', 'last_appointment_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at', 'last_appointment_at']

    fieldsets = (
        (_('Información del Cliente'), {
            'fields': ('tenant', 'name', 'phone', 'email')
        }),
        (_('Notas'), {
            'fields': ('notes',)
        }),
        (_('Información Adicional'), {
            'fields': ('last_appointment_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_appointments_display(self, obj):
        """Display total number of appointments."""
        count = obj.appointments.count()
        return f"{count} citas"
    total_appointments_display.short_description = _('Total de Citas')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'customer_name',
        'service_name',
        'tenant',
        'scheduled_at',
        'status_badge',
        'payment_status_badge',
        'total_amount_display',
    ]
    list_filter = [
        'status',
        'payment_status',
        'tenant',
        'service',
        'scheduled_at',
        'created_at',
    ]
    search_fields = [
        'customer__name',
        'customer__phone',
        'service__name',
        'internal_notes',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'confirmed_at',
        'cancelled_at',
        'completed_at',
    ]
    date_hierarchy = 'scheduled_at'

    fieldsets = (
        (_('Información de la Cita'), {
            'fields': ('tenant', 'service', 'customer', 'scheduled_at', 'duration_minutes')
        }),
        (_('Estado'), {
            'fields': ('status', 'payment_status')
        }),
        (_('Pago'), {
            'fields': ('total_amount', 'currency', 'payment_proof_media_id', 'bancard_transaction_id')
        }),
        (_('Integración'), {
            'fields': ('google_calendar_event_id',),
            'classes': ('collapse',)
        }),
        (_('Notas'), {
            'fields': ('customer_notes', 'internal_notes')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'cancelled_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'confirm_appointments',
        'cancel_appointments',
        'complete_appointments',
        'mark_no_show_appointments',
    ]

    def customer_name(self, obj):
        """Display customer name."""
        return obj.customer.name
    customer_name.short_description = _('Cliente')

    def service_name(self, obj):
        """Display service name."""
        return obj.service.name
    service_name.short_description = _('Servicio')

    def total_amount_display(self, obj):
        """Format total amount with currency."""
        return f"{obj.currency} {obj.total_amount}"
    total_amount_display.short_description = _('Monto')

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            AppointmentStatus.PENDING: '#FFA500',  # Orange
            AppointmentStatus.CONFIRMED: '#28a745',  # Green
            AppointmentStatus.CANCELLED: '#dc3545',  # Red
            AppointmentStatus.COMPLETED: '#007bff',  # Blue
            AppointmentStatus.NO_SHOW: '#6c757d',  # Gray
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Estado')

    def payment_status_badge(self, obj):
        """Display payment status as colored badge."""
        colors = {
            'PENDING': '#FFA500',  # Orange
            'PAID': '#28a745',  # Green
            'REFUNDED': '#6c757d',  # Gray
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = _('Pago')

    @admin.action(description=_("Confirmar citas seleccionadas"))
    def confirm_appointments(self, request, queryset):
        """Admin action to confirm multiple appointments."""
        success = 0
        errors = 0

        for appointment in queryset:
            try:
                confirm_appointment(appointment)
                success += 1
            except BookingError:
                errors += 1

        if success:
            self.message_user(
                request,
                f"{success} cita(s) confirmada(s) exitosamente"
            )
        if errors:
            self.message_user(
                request,
                f"{errors} cita(s) no pudieron ser confirmadas",
                level='warning'
            )

    @admin.action(description=_("Cancelar citas seleccionadas"))
    def cancel_appointments(self, request, queryset):
        """Admin action to cancel multiple appointments."""
        success = 0

        for appointment in queryset:
            try:
                cancel_appointment(appointment, reason="Cancelación admin masiva")
                success += 1
            except BookingError:
                pass

        if success:
            self.message_user(
                request,
                f"{success} cita(s) cancelada(s) exitosamente"
            )

    @admin.action(description=_("Marcar como completadas"))
    def complete_appointments(self, request, queryset):
        """Admin action to mark appointments as completed."""
        success = 0
        errors = 0

        for appointment in queryset:
            try:
                complete_appointment(appointment)
                success += 1
            except BookingError:
                errors += 1

        if success:
            self.message_user(
                request,
                f"{success} cita(s) marcada(s) como completada(s)"
            )
        if errors:
            self.message_user(
                request,
                f"{errors} cita(s) no pudieron ser completadas",
                level='warning'
            )

    @admin.action(description=_("Marcar como 'No Show'"))
    def mark_no_show_appointments(self, request, queryset):
        """Admin action to mark appointments as no-show."""
        success = 0
        errors = 0

        for appointment in queryset:
            try:
                mark_no_show(appointment)
                success += 1
            except BookingError:
                errors += 1

        if success:
            self.message_user(
                request,
                f"{success} cita(s) marcada(s) como 'No Show'"
            )
        if errors:
            self.message_user(
                request,
                f"{errors} cita(s) no pudieron ser marcadas como 'No Show'",
                level='warning'
            )
