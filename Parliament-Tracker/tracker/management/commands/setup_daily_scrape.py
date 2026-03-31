# tracker/management/commands/setup_daily_scrape.py
from django.core.management.base import BaseCommand
from django_q.models import Schedule

class Command(BaseCommand):
    help = 'Setup daily scraping at 9 AM'

    def handle(self, *args, **options):
        Schedule.objects.create(
            name='Daily bill scrape',
            func='tracker.management.commands.scrape_today.Command.handle',
            schedule_type=Schedule.DAILY,
            repeats=-1
        )
        self.stdout.write(self.style.SUCCESS("✅ Daily scraping scheduled at 9 AM"))