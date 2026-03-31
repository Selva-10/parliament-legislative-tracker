# tracker/management/commands/scrape_today.py
from django.core.management.base import BaseCommand
from tracker.scraper import RealBillScraper

class Command(BaseCommand):
    help = 'Scrape today\'s bills with minister and party details'

    def handle(self, *args, **options):
        scraper = RealBillScraper()
        bills = scraper.scrape_today_bills()
        if bills:
            scraper.save_bills(bills)
            self.stdout.write(self.style.SUCCESS(f'✅ Added/updated {len(bills)} bills'))
        else:
            self.stdout.write(self.style.WARNING('No bills scraped'))