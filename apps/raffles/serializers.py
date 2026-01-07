from rest_framework import serializers
from apps.raffles.models import Raffle, Order, TicketNumber, OrderTicket


class RaffleSerializer(serializers.ModelSerializer):
    available_count = serializers.IntegerField(read_only=True)
    sold_count = serializers.IntegerField(read_only=True)
    reserved_count = serializers.IntegerField(read_only=True)
    total_tickets = serializers.IntegerField(read_only=True)

    class Meta:
        model = Raffle
        fields = [
            'id',
            'title',
            'description',
            'ticket_price',
            'currency',
            'is_active',
            'min_number',
            'max_number',
            'total_tickets',
            'available_count',
            'sold_count',
            'reserved_count',
            'created_at',
            'updated_at',
            'draw_date',
            'winner_number',
        ]


class TicketNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketNumber
        fields = [
            'id',
            'number',
            'status',
            'reserved_until',
            'created_at',
            'updated_at',
        ]


class OrderTicketSerializer(serializers.ModelSerializer):
    ticket_number = serializers.IntegerField(source='ticket.number', read_only=True)

    class Meta:
        model = OrderTicket
        fields = ['id', 'ticket_number', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    raffle_title = serializers.CharField(source='raffle.title', read_only=True)
    contact_wa_id = serializers.CharField(source='contact.wa_id', read_only=True)
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    tickets = OrderTicketSerializer(source='order_tickets', many=True, read_only=True)
    ticket_numbers = serializers.ListField(child=serializers.IntegerField(), read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'raffle',
            'raffle_title',
            'contact',
            'contact_wa_id',
            'contact_name',
            'qty',
            'total_amount',
            'status',
            'payment_proof_media_id',
            'created_at',
            'updated_at',
            'paid_at',
            'expires_at',
            'tickets',
            'ticket_numbers',
        ]
        read_only_fields = [
            'total_amount',
            'created_at',
            'updated_at',
            'paid_at',
        ]


class ConfirmPaymentSerializer(serializers.Serializer):
    payment_proof_media_id = serializers.CharField(required=False, allow_blank=True)
