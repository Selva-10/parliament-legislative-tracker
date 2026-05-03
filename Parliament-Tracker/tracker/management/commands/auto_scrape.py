# tracker/management/commands/auto_scrape.py
from django.core.management.base import BaseCommand
from tracker.auto_scraper import auto_scraper, manual_scrape_all
import time
import sys

class Command(BaseCommand):
    help = 'Run automatic bill scraper for MPA and PRS India'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run scraping once and exit'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as a daemon (continuous mode)'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show scraper status'
        )
        parser.add_argument(
            '--stop',
            action='store_true',
            help='Stop the running scraper'
        )
    
    def handle(self, *args, **options):
        if options['status']:
            status = auto_scraper.get_status()
            self.stdout.write("\n📊 Auto-Scraper Status:")
            self.stdout.write(f"   Running: {status['running']}")
            self.stdout.write(f"   Scraping in progress: {status['scraping_in_progress']}")
            self.stdout.write(f"   Last run: {status['last_run']}")
            self.stdout.write(f"   Thread alive: {status['thread_alive']}")
            return
        
        if options['stop']:
            auto_scraper.stop_scheduler()
            self.stdout.write(self.style.SUCCESS("✅ Scraper stopped"))
            return
        
        if options['once']:
            self.stdout.write(self.style.WARNING("🔄 Running manual scrape (once)..."))
            results = manual_scrape_all()
            self.stdout.write(self.style.SUCCESS(f"✅ Scrape complete: {results}"))
            return
        
        if options['daemon']:
            self.stdout.write(self.style.SUCCESS("🚀 Starting auto-scraper daemon..."))
            auto_scraper.run_scheduler()
        else:
            self.stdout.write(self.style.SUCCESS("🚀 Starting auto-scraper in background..."))
            auto_scraper.start_scheduler()
            self.stdout.write("Press Ctrl+C to stop")
            
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                auto_scraper.stop_scheduler()
                self.stdout.write(self.style.WARNING("\n🛑 Scraper stopped"))