from django.core.management.base import BaseCommand, CommandError
from apps.raffles.models import Raffle, TicketNumber


class Command(BaseCommand):
    help = 'Generate ticket numbers for a raffle'

    def add_arguments(self, parser):
        parser.add_argument(
            'raffle_id',
            type=int,
            help='ID of the raffle to generate tickets for'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if tickets already exist'
        )

    def handle(self, **options):
        raffle_id = options['raffle_id']
        force = options.get('force', False)

        try:
            raffle = Raffle.objects.get(id=raffle_id)
        except Raffle.DoesNotExist:
            raise CommandError(f'Raffle with ID {raffle_id} does not exist')

        existing_count = TicketNumber.objects.filter(raffle=raffle).count()

        if existing_count > 0 and not force:
            raise CommandError(
                f'Raffle "{raffle.title}" already has {existing_count} tickets. '
                f'Use --force to regenerate.'
            )

        if force and existing_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Deleting {existing_count} existing tickets...')
            )
            TicketNumber.objects.filter(raffle=raffle).delete()

        # Generate tickets
        total_tickets = raffle.max_number - raffle.min_number + 1
        self.stdout.write(f'Generating {total_tickets} tickets for "{raffle.title}"...')

        tickets = [
            TicketNumber(raffle=raffle, number=num)
            for num in range(raffle.min_number, raffle.max_number + 1)
        ]

        TicketNumber.objects.bulk_create(tickets, batch_size=1000)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {len(tickets)} tickets for raffle "{raffle.title}"'
            )
        )
