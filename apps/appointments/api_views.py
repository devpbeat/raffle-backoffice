from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.dateparse import parse_date

from apps.appointments.models import Service, Customer, Appointment
from apps.appointments.serializers import (
    ServiceSerializer,
    CustomerSerializer,
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    CreateAppointmentSerializer,
    ConfirmAppointmentSerializer,
    CancelAppointmentSerializer,
    AvailabilityQuerySerializer,
    AvailabilityResponseSerializer,
)
from apps.appointments.services.bookings import (
    create_appointment,
    confirm_appointment,
    cancel_appointment,
    complete_appointment,
    mark_no_show,
    BookingError,
)
from apps.appointments.services.availability import get_available_slots


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing services (tenant-scoped).

    Endpoints:
    - GET /services/ - List all services for tenant
    - POST /services/ - Create new service
    - GET /services/{id}/ - Get service details
    - PUT /services/{id}/ - Update service
    - PATCH /services/{id}/ - Partial update service
    - DELETE /services/{id}/ - Delete service
    """
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']

    def get_queryset(self):
        """Filter services by tenant from request."""
        if not self.request.tenant:
            return Service.objects.none()

        return Service.objects.filter(
            tenant=self.request.tenant
        ).order_by('name')

    def perform_create(self, serializer):
        """Automatically set tenant when creating service."""
        if not self.request.tenant:
            raise ValidationError({'detail': 'No se pudo identificar el tenant'})

        serializer.save(tenant=self.request.tenant)


class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing customers (tenant-scoped).

    Endpoints:
    - GET /customers/ - List all customers for tenant
    - POST /customers/ - Create new customer
    - GET /customers/{id}/ - Get customer details
    - PUT /customers/{id}/ - Update customer
    - PATCH /customers/{id}/ - Partial update customer
    - DELETE /customers/{id}/ - Delete customer
    """
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['phone', 'email']

    def get_queryset(self):
        """Filter customers by tenant from request."""
        if not self.request.tenant:
            return Customer.objects.none()

        return Customer.objects.filter(
            tenant=self.request.tenant
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Automatically set tenant when creating customer."""
        if not self.request.tenant:
            raise ValidationError({'detail': 'No se pudo identificar el tenant'})

        serializer.save(tenant=self.request.tenant)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing appointments (tenant-scoped).

    Endpoints:
    - GET /appointments/ - List all appointments for tenant
    - POST /appointments/ - Create new appointment
    - GET /appointments/{id}/ - Get appointment details
    - PUT /appointments/{id}/ - Update appointment
    - PATCH /appointments/{id}/ - Partial update appointment
    - DELETE /appointments/{id}/ - Delete appointment
    - POST /appointments/{id}/confirm/ - Confirm appointment
    - POST /appointments/{id}/cancel/ - Cancel appointment
    - POST /appointments/{id}/complete/ - Mark as completed
    - POST /appointments/{id}/no_show/ - Mark as no-show
    - GET /appointments/availability/ - Check availability
    """
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_status', 'service', 'customer']

    def get_queryset(self):
        """Filter appointments by tenant from request."""
        if not self.request.tenant:
            return Appointment.objects.none()

        queryset = Appointment.objects.filter(
            tenant=self.request.tenant
        ).select_related('service', 'customer').order_by('-scheduled_at')

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(scheduled_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_at__lte=end_date)

        return queryset

    def get_serializer_class(self):
        """Use different serializers for list and detail views."""
        if self.action == 'list':
            return AppointmentListSerializer
        elif self.action == 'create':
            return CreateAppointmentSerializer
        else:
            return AppointmentDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create a new appointment using the service layer."""
        if not request.tenant:
            return Response(
                {'detail': 'No se pudo identificar el tenant'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Use service layer to create appointment
            appointment = create_appointment(
                tenant=request.tenant,
                service_id=serializer.validated_data['service'].id,
                customer_data=serializer.validated_data['customer_data'],
                scheduled_at=serializer.validated_data['scheduled_at'],
                notes=serializer.validated_data.get('customer_notes', '')
            )

            # Return the created appointment with detail serializer
            response_serializer = AppointmentDetailSerializer(appointment)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except BookingError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """
        Confirm an appointment and mark as paid.

        POST /appointments/{id}/confirm/
        Body: {"payment_transaction_id": "optional"}
        """
        appointment = self.get_object()

        serializer = ConfirmAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment_id = serializer.validated_data.get('payment_transaction_id')
            updated = confirm_appointment(appointment, payment_id)

            # Sync to Google Calendar if available
            # This will be implemented in Phase 4
            try:
                from apps.integrations.services.google_calendar import sync_appointment_to_calendar
                sync_appointment_to_calendar(updated)
            except ImportError:
                # Integrations app not yet created
                pass

            response_serializer = AppointmentDetailSerializer(updated)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        except BookingError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Cancel an appointment.

        POST /appointments/{id}/cancel/
        Body: {"reason": "optional"}
        """
        appointment = self.get_object()

        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reason = serializer.validated_data.get('reason', '')
            updated = cancel_appointment(appointment, reason)

            response_serializer = AppointmentDetailSerializer(updated)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        except BookingError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """
        Mark an appointment as completed.

        POST /appointments/{id}/complete/
        """
        appointment = self.get_object()

        try:
            updated = complete_appointment(appointment)

            response_serializer = AppointmentDetailSerializer(updated)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        except BookingError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='no-show')
    def no_show(self, request, pk=None):
        """
        Mark an appointment as no-show.

        POST /appointments/{id}/no-show/
        """
        appointment = self.get_object()

        try:
            updated = mark_no_show(appointment)

            response_serializer = AppointmentDetailSerializer(updated)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        except BookingError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='availability')
    def availability(self, request):
        """
        Get available slots for a service on a date.

        GET /appointments/availability/?service=1&date=2026-01-10

        Query Parameters:
        - service (int): Service ID
        - date (str): Date in YYYY-MM-DD format

        Returns:
        - service_id (int)
        - service_name (str)
        - date (str)
        - available_slots (list): List of available datetime strings
        - total_slots (int): Total number of available slots
        """
        if not request.tenant:
            return Response(
                {'error': 'No se pudo identificar el tenant'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate query parameters
        service_id = request.query_params.get('service')
        date_str = request.query_params.get('date')

        if not service_id or not date_str:
            return Response(
                {'error': 'Se requieren los parámetros "service" y "date"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = Service.objects.get(
                id=service_id,
                tenant=request.tenant,
                is_active=True
            )
        except Service.DoesNotExist:
            return Response(
                {'error': 'Servicio no encontrado o inactivo'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            date = parse_date(date_str)
            if not date:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get available slots
        slots = get_available_slots(request.tenant, service, date)

        return Response({
            'service_id': service.id,
            'service_name': service.name,
            'date': date_str,
            'available_slots': [slot.isoformat() for slot in slots],
            'total_slots': len(slots)
        })
