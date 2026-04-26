from django.core.management.base import BaseCommand
from tracker.scraper import RealBillScraper
import csv
from datetime import datetime

class Command(BaseCommand):
    help = 'Import bills from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def handle(self, self_filename, *args, **options):
        csv_path = options['csv_file']
        
        self.stdout.write(f"Importing bills from {csv_path}")
        
        with open(csv_path, 'r') as f:
            content = f.read()
        
        scraper = RealBillScraper()
        bills = scraper.scrape_bills_from_csv(content)
        
        self.stdout.write(f"Imported {len(bills)} bills")