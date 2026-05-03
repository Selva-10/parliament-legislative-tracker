# tracker/management/commands/scrape_today.py
from django.core.management.base import BaseCommand
from tracker.auto_scraper import manual_scrape_all
from datetime import datetime

class Command(BaseCommand):
    help = 'Scrape bills from MPA and PRS India'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['mpa', 'prs', 'all'],
            default='all',
            help='Source to scrape (mpa, prs, or all)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(f"\n📡 Starting scrape at {datetime.now()}")
        self.stdout.write("=" * 50)
        
        try:
            results = manual_scrape_all()
            
            self.stdout.write("\n📊 Scraping Results:")
            self.stdout.write(f"   MPA Bills: {results.get('mpa', 0)}")
            self.stdout.write(f"   PRS Bills: {results.get('prs', 0)}")
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Scrape completed at {datetime.now()}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Scrape failed: {e}"))