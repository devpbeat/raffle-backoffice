from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from apps.raffles.models import Raffle, Order, TicketNumber, OrderStatus
from apps.raffles.serializers import (
    RaffleSerializer,
    OrderSerializer,
    TicketNumberSerializer,
    ConfirmPaymentSerializer,
)
from apps.raffles.services import confirm_paid, release_order_reservations, ReservationError
import logging

logger = logging.getLogger(__name__)


class RaffleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing raffles.
    """
    queryset = Raffle.objects.all().order_by('-created_at')
    serializer_class = RaffleSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Get availability information for a raffle.
        GET /api/raffles/{id}/availability/
        """
        raffle = self.get_object()

        available_tickets = TicketNumber.objects.filter(
            raffle=raffle,
            status='AVAILABLE'
        ).values_list('number', flat=True).order_by('number')

        return Response({
            'raffle_id': raffle.id,
            'total_tickets': raffle.total_tickets,
            'available_count': raffle.available_count,
            'sold_count': raffle.sold_count,
            'reserved_count': raffle.reserved_count,
            'available_numbers': list(available_tickets),
        })

    @action(detail=True, methods=['get'])
    def tickets(self, request, pk=None):
        """
        Get all tickets for a raffle with their statuses.
        GET /api/raffles/{id}/tickets/
        """
        raffle = self.get_object()
        tickets = TicketNumber.objects.filter(raffle=raffle).order_by('number')
        serializer = TicketNumberSerializer(tickets, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    """
    queryset = Order.objects.all().select_related('raffle', 'contact').order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'raffle', 'contact']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status via query param
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        """
        Confirm payment for an order.
        POST /api/orders/{id}/confirm-payment/
        Body: {"payment_proof_media_id": "optional_media_id"}
        """
        order = self.get_object()

        if order.status != OrderStatus.PENDING_PAYMENT:
            return Response(
                {'error': f'Cannot confirm order with status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ConfirmPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment_proof_media_id = serializer.validated_data.get('payment_proof_media_id')
            updated_order = confirm_paid(order, payment_proof_media_id)

            logger.info(f"Order {order.id} confirmed by admin {request.user}")

            return Response(
                OrderSerializer(updated_order).data,
                status=status.HTTP_200_OK
            )

        except ReservationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an order and release its tickets.
        POST /api/orders/{id}/cancel/
        """
        order = self.get_object()

        if order.status not in [OrderStatus.DRAFT, OrderStatus.PENDING_PAYMENT]:
            return Response(
                {'error': f'Cannot cancel order with status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            released_count = release_order_reservations(order)

            logger.info(f"Order {order.id} cancelled by admin {request.user}, released {released_count} tickets")

            return Response(
                {
                    'message': 'Order cancelled successfully',
                    'released_tickets': released_count,
                    'order': OrderSerializer(order).data
                },
                status=status.HTTP_200_OK
            )

        except ReservationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def pending_payment(self, request):
        """
        Get all orders pending payment.
        GET /api/orders/pending-payment/
        """
        orders = Order.objects.filter(
            status=OrderStatus.PENDING_PAYMENT
        ).select_related('raffle', 'contact').order_by('-created_at')

        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
