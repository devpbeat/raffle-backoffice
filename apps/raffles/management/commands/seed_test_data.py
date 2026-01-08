from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.raffles.models import Raffle, TicketNumber, Order, OrderTicket, OrderStatus, TicketStatus
from apps.whatsapp.models import WhatsAppContact


class Command(BaseCommand):
    help = 'Seed test data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before seeding'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            OrderTicket.objects.all().delete()
            Order.objects.all().delete()
            TicketNumber.objects.all().delete()
            Raffle.objects.all().delete()
            WhatsAppContact.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all data.'))

        # Create test contacts
        self.stdout.write('Creating test contacts...')
        contacts = []
        test_contacts = [
            {'wa_id': '573001234567', 'name': 'Juan Pérez', 'state': 'MENU'},
            {'wa_id': '573009876543', 'name': 'María García', 'state': 'MENU'},
            {'wa_id': '573005551234', 'name': 'Carlos López', 'state': 'MENU'},
            {'wa_id': '573008889999', 'name': 'Ana Martínez', 'state': 'MENU'},
            {'wa_id': '573002223333', 'name': 'Test User', 'state': 'MENU'},
        ]
        for data in test_contacts:
            contact, created = WhatsAppContact.objects.get_or_create(
                wa_id=data['wa_id'],
                defaults={'name': data['name'], 'state': data['state'], 'context': {}}
            )
            contacts.append(contact)
            if created:
                self.stdout.write(f'  Created contact: {contact.name} ({contact.wa_id})')
            else:
                self.stdout.write(f'  Exists: {contact.name} ({contact.wa_id})')

        # Create test raffle
        self.stdout.write('Creating test raffle...')
        raffle, created = Raffle.objects.get_or_create(
            title='Gran Rifa de Navidad 2026',
            defaults={
                'description': 'Participa y gana increíbles premios!',
                'ticket_price': Decimal('10000.00'),
                'currency': 'COP',
                'is_active': True,
                'min_number': 1,
                'max_number': 1000,
                'draw_date': timezone.now() + timedelta(days=30),
            }
        )
        if created:
            self.stdout.write(f'  Created raffle: {raffle.title}')
        else:
            self.stdout.write(f'  Exists: {raffle.title}')

        # Generate tickets if not exists
        ticket_count = TicketNumber.objects.filter(raffle=raffle).count()
        if ticket_count == 0:
            self.stdout.write('Generating tickets...')
            tickets = [
                TicketNumber(raffle=raffle, number=num)
                for num in range(raffle.min_number, raffle.max_number + 1)
            ]
            TicketNumber.objects.bulk_create(tickets, batch_size=500)
            self.stdout.write(f'  Created {len(tickets)} tickets')
        else:
            self.stdout.write(f'  Tickets exist: {ticket_count}')

        # Create sample orders
        self.stdout.write('Creating sample orders...')
        
        # Get available tickets
        available_tickets = list(
            TicketNumber.objects.filter(raffle=raffle, status=TicketStatus.AVAILABLE)
            .order_by('number')[:50]
        )
        
        if len(available_tickets) >= 20:
            # Order 1: PAID order
            order1, created = Order.objects.get_or_create(
                raffle=raffle,
                contact=contacts[0],
                status=OrderStatus.PAID,
                defaults={
                    'qty': 5,
                    'total_amount': raffle.ticket_price * 5,
                    'paid_at': timezone.now() - timedelta(hours=2),
                }
            )
            if created:
                for ticket in available_tickets[0:5]:
                    ticket.status = TicketStatus.SOLD
                    ticket.save()
                    OrderTicket.objects.create(order=order1, ticket=ticket)
                self.stdout.write(f'  Created PAID order #{order1.id}')

            # Order 2: PENDING_PAYMENT order
            order2, created = Order.objects.get_or_create(
                raffle=raffle,
                contact=contacts[1],
                status=OrderStatus.PENDING_PAYMENT,
                defaults={
                    'qty': 3,
                    'total_amount': raffle.ticket_price * 3,
                    'expires_at': timezone.now() + timedelta(minutes=30),
                }
            )
            if created:
                for ticket in available_tickets[5:8]:
                    ticket.status = TicketStatus.RESERVED
                    ticket.reserved_by_order = order2
                    ticket.reserved_until = timezone.now() + timedelta(minutes=30)
                    ticket.save()
                    OrderTicket.objects.create(order=order2, ticket=ticket)
                self.stdout.write(f'  Created PENDING_PAYMENT order #{order2.id}')

            # Order 3: DRAFT order
            order3, created = Order.objects.get_or_create(
                raffle=raffle,
                contact=contacts[2],
                status=OrderStatus.DRAFT,
                defaults={
                    'qty': 2,
                    'total_amount': raffle.ticket_price * 2,
                }
            )
            if created:
                for ticket in available_tickets[8:10]:
                    ticket.status = TicketStatus.RESERVED
                    ticket.reserved_by_order = order3
                    ticket.reserved_until = timezone.now() + timedelta(minutes=30)
                    ticket.save()
                    OrderTicket.objects.create(order=order3, ticket=ticket)
                self.stdout.write(f'  Created DRAFT order #{order3.id}')

        self.stdout.write(self.style.SUCCESS('\n✅ Test data seeded successfully!'))
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  Contacts: {WhatsAppContact.objects.count()}')
        self.stdout.write(f'  Raffles: {Raffle.objects.count()}')
        self.stdout.write(f'  Tickets: {TicketNumber.objects.count()}')
        self.stdout.write(f'  Orders: {Order.objects.count()}')
        self.stdout.write(f'\nYou can now test the admin at http://localhost:8000/admin/')
