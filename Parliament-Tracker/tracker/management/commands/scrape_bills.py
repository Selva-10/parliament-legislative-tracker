from django.core.management.base import BaseCommand
from tracker.scraper import RealBillScraper
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape bills from MPA website and other sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['mpa', 'all'],
            default='mpa',
            help='Source to scrape from (default: mpa)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing bills before scraping'
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("STARTING BILL SCRAPER")
        self.stdout.write("=" * 60)
        
        if options['clear']:
            from tracker.models import Bill
            count = Bill.objects.count()
            Bill.objects.all().delete()
            self.stdout.write(f"✓ Cleared {count} existing bills")
        
        scraper = RealBillScraper()
        
        if options['source'] == 'mpa':
            self.stdout.write("\n📋 Scraping from MPA website...")
            result = scraper.scrape_all()
        else:
            result = scraper.scrape_all()
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"SCRAPING RESULTS:")
        self.stdout.write(f"  - Created: {result['created']}")
        self.stdout.write(f"  - Updated: {result['updated']}")
        self.stdout.write(f"  - Failed: {result['failed']}")
        self.stdout.write("=" * 60)