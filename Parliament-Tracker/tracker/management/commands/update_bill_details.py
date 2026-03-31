# tracker/management/commands/update_bill_details.py
from django.core.management.base import BaseCommand
from tracker.models import Bill
from tracker.scraper import RealBillScraper
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update bill numbers and introducers for existing bills'

    def handle(self, *args, **options):
        scraper = RealBillScraper()
        bills = Bill.objects.filter(source='MPA').exclude(source_url__isnull=True).exclude(source_url='')
        updated = 0
        failed = 0
        for bill in bills:
            try:
                details = scraper.fetch_bill_details(bill.source_url)
                if details:
                    if 'bill_number' in details:
                        bill.bill_number = details['bill_number']
                    if 'introduced_by' in details:
                        bill.introduced_by = details['introduced_by']
                    bill.save()
                    updated += 1
                    self.stdout.write(f"Updated {bill.bill_id}")
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"Failed {bill.bill_id}: {e}"))
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated}, Failed: {failed}"))