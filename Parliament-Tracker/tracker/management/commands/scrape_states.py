# tracker/management/commands/scrape_states.py
from django.core.management.base import BaseCommand
from tracker.state_scraper import scrape_all_state_bills
from datetime import datetime

class Command(BaseCommand):
    help = 'Scrape bills from all Indian states'
    
    def handle(self, *args, **options):
        self.stdout.write(f"\nStarting state bills scrape at {datetime.now()}")
        self.stdout.write("=" * 50)
        
        try:
            saved = scrape_all_state_bills()
            self.stdout.write(self.style.SUCCESS(f"\n✅ State bills scraped: {saved} bills saved"))
            self.stdout.write(f"Completed at {datetime.now()}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Scrape failed: {e}"))