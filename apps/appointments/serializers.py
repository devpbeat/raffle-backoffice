from rest_framework import serializers
from apps.appointments.models import Service, Customer, Appointment


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model."""

    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'description',
            'duration_minutes',
            'price',
            'currency',
            'is_active',
            'buffer_time_minutes',
            'max_bookings_per_day',
            'advance_booking_days',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model."""

    total_appointments = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'notes',
            'created_at',
            'updated_at',
            'last_appointment_at',
            'total_appointments',
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_appointment_at']

    def get_total_appointments(self, obj):
        """Get total number of appointments for this customer."""
        return obj.appointments.count()


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing appointments (lighter data)."""

    service_name = serializers.CharField(source='service.name', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'service',
            'service_name',
            'customer',
            'customer_name',
            'customer_phone',
            'scheduled_at',
            'duration_minutes',
            'status',
            'status_display',
            'payment_status',
            'payment_status_display',
            'total_amount',
            'currency',
            'created_at',
        ]


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for appointment details (full data)."""

    service = ServiceSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    end_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'service',
            'customer',
            'scheduled_at',
            'end_time',
            'duration_minutes',
            'status',
            'status_display',
            'payment_status',
            'payment_status_display',
            'total_amount',
            'currency',
            'payment_proof_media_id',
            'bancard_transaction_id',
            'google_calendar_event_id',
            'customer_notes',
            'internal_notes',
            'created_at',
            'updated_at',
            'confirmed_at',
            'cancelled_at',
            'completed_at',
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
            'confirmed_at',
            'cancelled_at',
            'completed_at',
            'end_time',
        ]


class CreateAppointmentSerializer(serializers.Serializer):
    """Serializer for creating a new appointment."""

    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        help_text="ID del servicio a reservar"
    )
    customer_data = serializers.DictField(
        help_text="Datos del cliente: {name, phone, email (opcional)}"
    )
    scheduled_at = serializers.DateTimeField(
        help_text="Fecha y hora de la cita"
    )
    customer_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notas del cliente"
    )

    def validate_customer_data(self, value):
        """Validate customer data structure."""
        if 'name' not in value:
            raise serializers.ValidationError("El campo 'name' es requerido en customer_data")
        if 'phone' not in value:
            raise serializers.ValidationError("El campo 'phone' es requerido en customer_data")
        return value

    def validate_service(self, value):
        """Validate service is active."""
        if not value.is_active:
            raise serializers.ValidationError("Este servicio no está activo")
        return value


class ConfirmAppointmentSerializer(serializers.Serializer):
    """Serializer for confirming an appointment."""

    payment_transaction_id = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="ID de la transacción de pago (opcional)"
    )


class CancelAppointmentSerializer(serializers.Serializer):
    """Serializer for canceling an appointment."""

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Razón de la cancelación (opcional)"
    )


class AvailabilityQuerySerializer(serializers.Serializer):
    """Serializer for availability query parameters."""

    service = serializers.IntegerField(
        help_text="ID del servicio"
    )
    date = serializers.DateField(
        help_text="Fecha para consultar disponibilidad (YYYY-MM-DD)"
    )


class AvailabilityResponseSerializer(serializers.Serializer):
    """Serializer for availability response."""

    service_id = serializers.IntegerField()
    service_name = serializers.CharField()
    date = serializers.DateField()
    available_slots = serializers.ListField(
        child=serializers.DateTimeField(),
        help_text="Lista de horarios disponibles"
    )
    total_slots = serializers.IntegerField()
