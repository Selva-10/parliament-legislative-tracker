# tracker/management/commands/fetch_realtime.py
from django.core.management.base import BaseCommand
from tracker.models import Bill
import requests
from datetime import datetime

class Command(BaseCommand):
    help = 'Fetch real-time bill data from government API'

    def handle(self, *args, **options):
        # Try multiple sources
        sources = [
            self.fetch_from_prs,
            self.fetch_from_sansad,
            self.generate_fallback
        ]
        
        for source in sources:
            bills = source()
            if bills:
                for bill in bills:
                    Bill.objects.update_or_create(
                        bill_id=bill['bill_id'],
                        defaults=bill
                    )
                self.stdout.write(self.style.SUCCESS(f"✅ Added {len(bills)} bills"))
                break

    def fetch_from_prs(self):
        # PRS India scraper code here
        pass

    def fetch_from_sansad(self):
        # Sansad.in scraper code here
        pass

    def generate_fallback(self):
        # Generate realistic bills if all sources fail
        return []