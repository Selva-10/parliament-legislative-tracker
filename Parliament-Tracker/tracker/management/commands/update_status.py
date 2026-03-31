# tracker/management/commands/update_status.py
from django.core.management.base import BaseCommand
from tracker.scraper import RealBillScraper
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update status of pending bills from government sources'
    
    def add_arguments(self, parser):
        parser.add_argument('--bill-id', type=str, help='Update specific bill only')
        parser.add_argument('--all', action='store_true', help='Update all pending bills')
    
    def handle(self, *args, **options):
        scraper = RealBillScraper()
        
        if options['bill_id']:
            self.stdout.write(f"Updating status for bill: {options['bill_id']}")
            result = scraper.update_bill_status(options['bill_id'])
            if result:
                self.stdout.write(self.style.SUCCESS(f"Bill {options['bill_id']} updated"))
            else:
                self.stdout.write(self.style.WARNING(f"Bill {options['bill_id']} not updated"))
        
        elif options['all']:
            self.stdout.write("Updating status for all pending bills...")
            results = scraper.update_all_statuses()
            self.stdout.write(self.style.SUCCESS(f"Updated: {results['updated']}, Failed: {results['failed']}"))
        
        else:
            self.stdout.write(self.style.WARNING("Please specify --bill-id or --all"))