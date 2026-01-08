from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create an operator user with limited permissions (can only confirm payments)'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the operator')
        parser.add_argument('password', type=str, help='Password for the operator')
        parser.add_argument('--email', type=str, default='', help='Email for the operator')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options.get('email', '')

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"User '{username}' already exists. Updating permissions...")
            )
            user = User.objects.get(username=username)
        else:
            # Create the user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                is_staff=True,  # Needed to access admin
                is_superuser=False  # NOT a superuser
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created operator user: {username}")
            )

        # Get content types for the models we want to give access to
        from apps.raffles.models import Order, Raffle, TicketNumber, OrderTicket
        
        # Clear existing permissions
        user.user_permissions.clear()

        # Order permissions - view and change only
        order_ct = ContentType.objects.get_for_model(Order)
        order_perms = Permission.objects.filter(
            content_type=order_ct,
            codename__in=['view_order', 'change_order']
        )
        user.user_permissions.add(*order_perms)

        # Raffle - view only
        raffle_ct = ContentType.objects.get_for_model(Raffle)
        raffle_view = Permission.objects.get(content_type=raffle_ct, codename='view_raffle')
        user.user_permissions.add(raffle_view)

        # TicketNumber - view only
        ticket_ct = ContentType.objects.get_for_model(TicketNumber)
        ticket_view = Permission.objects.get(content_type=ticket_ct, codename='view_ticketnumber')
        user.user_permissions.add(ticket_view)

        # OrderTicket - view only
        order_ticket_ct = ContentType.objects.get_for_model(OrderTicket)
        order_ticket_view = Permission.objects.get(content_type=order_ticket_ct, codename='view_orderticket')
        user.user_permissions.add(order_ticket_view)

        # WhatsApp models - view only
        from apps.whatsapp.models import WhatsAppContact, InboundMessage
        
        contact_ct = ContentType.objects.get_for_model(WhatsAppContact)
        contact_view = Permission.objects.get(content_type=contact_ct, codename='view_whatsappcontact')
        user.user_permissions.add(contact_view)

        message_ct = ContentType.objects.get_for_model(InboundMessage)
        message_view = Permission.objects.get(content_type=message_ct, codename='view_inboundmessage')
        user.user_permissions.add(message_view)

        user.save()

        self.stdout.write(self.style.SUCCESS(f"""
✅ Operator '{username}' configured successfully!

Permissions granted:
  📋 Órdenes: Ver y Editar (solo estado)
  🎫 Rifas: Solo Ver
  🔢 Boletos: Solo Ver
  📱 Contactos WhatsApp: Solo Ver
  ✉️ Mensajes: Solo Ver

Login at: /admin/
Username: {username}
Password: {password}

Note: This user can ONLY change the status of orders.
When they mark an order as PAID, WhatsApp notification is sent automatically.
        """))
