"""
properties/management/commands/seed_locations.py
One-time management command to populate the Location table with
Karachi areas defined in the proposal.
"""
from django.core.management.base import BaseCommand
from properties.models import Location

KARACHI_AREAS = [
    'Gulshan-e-Iqbal', 'DHA', 'Clifton', 'PECHS',
    'North Nazimabad', 'Nazimabad', 'Korangi', 'Landhi',
    'Saddar', 'Malir', 'Bahria Town', 'F.B. Area',
    'Scheme 33', 'Johar', 'Buffer Zone',
]


class Command(BaseCommand):
    help = 'Seed the Location table with predefined Karachi areas.'

    def handle(self, *args, **kwargs):
        created_count = 0
        for name in KARACHI_AREAS:
            _, created = Location.objects.get_or_create(name=name)
            if created:
                created_count += 1
                self.stdout.write(f'  + Created: {name}')
            else:
                self.stdout.write(f'  ~ Already exists: {name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {created_count} new location(s) created, '
                f'{len(KARACHI_AREAS) - created_count} already existed.'
            )
        )
