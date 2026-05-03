from django.core.management.base import BaseCommand
from tracker.integrated_scraper import integrated_scrape
from datetime import datetime

class Command(BaseCommand):
    help = 'Scrape MPA bills and enhance with PRS session house data'
    
    def handle(self, *args, **options):
        self.stdout.write(f"\n🚀 Starting integrated scrape at {datetime.now()}")
        self.stdout.write("=" * 60)
        
        try:
            result = integrated_scrape()
            self.stdout.write(self.style.SUCCESS(
                f"\n✅ Complete! Created: {result['created']}, Updated: {result['updated']}"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Failed: {e}"))