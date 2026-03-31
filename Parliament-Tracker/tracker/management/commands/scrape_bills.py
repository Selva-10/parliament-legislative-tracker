# tracker/management/commands/scrape_bills.py
from django.core.management.base import BaseCommand
from tracker.scraper import scrape_all_sources
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape bills from all sources'
    
    def add_arguments(self, parser):
        parser.add_argument('--source', type=str, default='all', 
                          choices=['all', 'PRS', 'LOK_SABHA', 'RAJYA_SABHA'])
    
    def handle(self, *args, **options):
        source = options['source']
        self.stdout.write(f"Starting scrape from {source}...")
        
        from tracker.scraper import scrape_prs, scrape_loksabha, scrape_rajyasabha
        
        if source == 'all':
            result = scrape_all_sources()
        elif source == 'PRS':
            result = scrape_prs()
        elif source == 'LOK_SABHA':
            result = scrape_loksabha()
        elif source == 'RAJYA_SABHA':
            result = scrape_rajyasabha()
        
        self.stdout.write(self.style.SUCCESS(f"Scrape completed: {result}"))