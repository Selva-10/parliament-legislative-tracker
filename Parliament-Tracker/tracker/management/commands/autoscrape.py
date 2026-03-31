# tracker/management/commands/autoscrape.py
import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from tracker.models import Bill
from datetime import date, timedelta
import random

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Auto-scrape bills continuously'
    
    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=3600, 
                          help='Scraping interval in seconds (default: 3600)')
        parser.add_argument('--once', action='store_true', 
                          help='Run once and exit')
    
    def handle(self, *args, **options):
        interval = options['interval']
        once = options['once']
        
        self.stdout.write(self.style.SUCCESS(f"Auto-scraper started (interval: {interval}s)"))
        
        while True:
            try:
                self.scrape_bills()
                
                if once:
                    break
                    
                self.stdout.write(f"Waiting {interval} seconds until next scrape...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\nAuto-scraper stopped by user"))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
                time.sleep(60)  # Wait a minute before retrying
    
    def scrape_bills(self):
        """Scrape bills and save to database"""
        self.stdout.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Scraping bills...")
        
        # Generate realistic mock data
        bills_data = self.generate_mock_data()
        
        created = 0
        updated = 0
        
        for bill_data in bills_data:
            bill, created_flag = Bill.objects.update_or_create(
                bill_id=bill_data['bill_id'],
                defaults=bill_data
            )
            if created_flag:
                created += 1
            else:
                updated += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"Scrape complete: {created} created, {updated} updated"
        ))
        
        return {'created': created, 'updated': updated}
    
    def generate_mock_data(self):
        """Generate realistic mock bill data"""
        bills = []
        
        # PRS India Bills
        prs_bills = [
            {
                'bill_id': 'PRS-001',
                'bill_number': 'Bill No. 1 of 2024',
                'title': 'Digital Personal Data Protection Bill, 2023',
                'house': 'LOK_SABHA',
                'status': 'PASSED',
                'introduction_date': date.today() - timedelta(days=30),
                'passed_date': date.today() - timedelta(days=5),
                'introduced_by': 'Minister of Electronics & IT',
                'introduced_by_party': 'BJP',
                'ministry': 'Ministry of Electronics and Information Technology',
                'description': 'A bill to provide for the processing of digital personal data in a manner that recognizes both the right of individuals to protect their personal data and the need to process such data for lawful purposes.',
                'objective': 'To protect the privacy of Indian citizens while promoting innovation and growth in the digital economy.',
                'prs_link': 'https://prsindia.org/bill-tracker/digital-personal-data-protection-bill-2023',
                'source': 'PRS',
                'tags': ['digital', 'privacy', 'data protection']
            },
            {
                'bill_id': 'PRS-002',
                'bill_number': 'Bill No. 2 of 2024',
                'title': 'The Constitution (One Hundred and Twenty-Eighth Amendment) Bill, 2023',
                'house': 'LOK_SABHA',
                'status': 'PENDING',
                'introduction_date': date.today() - timedelta(days=15),
                'introduced_by': 'Minister of Law and Justice',
                'introduced_by_party': 'BJP',
                'ministry': 'Ministry of Law and Justice',
                'description': 'A bill to provide for reservation of women in Parliament and State Legislatures.',
                'objective': 'To empower women and increase their participation in the legislative process.',
                'prs_link': 'https://prsindia.org/bill-tracker/womens-reservation-bill-2023',
                'source': 'PRS',
                'tags': ['women', 'reservation', 'constitution']
            },
            {
                'bill_id': 'PRS-003',
                'bill_number': 'Bill No. 3 of 2024',
                'title': 'The National Research Foundation Bill, 2023',
                'house': 'LOK_SABHA',
                'status': 'PASSED',
                'introduction_date': date.today() - timedelta(days=60),
                'passed_date': date.today() - timedelta(days=20),
                'introduced_by': 'Minister of Science and Technology',
                'introduced_by_party': 'BJP',
                'ministry': 'Ministry of Science and Technology',
                'description': 'A bill to establish the National Research Foundation to seed, grow and promote research and development across universities and institutions.',
                'objective': 'To strengthen the research ecosystem in India.',
                'prs_link': 'https://prsindia.org/bill-tracker/national-research-foundation-bill-2023',
                'source': 'PRS',
                'tags': ['research', 'education', 'science']
            }
        ]
        
        # Lok Sabha Bills
        ls_bills = [
            {
                'bill_id': 'LS-101',
                'bill_number': 'Bill No. 101 of 2024',
                'title': 'The Finance Bill, 2024',
                'house': 'LOK_SABHA',
                'status': 'PASSED',
                'introduction_date': date.today() - timedelta(days=45),
                'passed_date': date.today() - timedelta(days=10),
                'introduced_by': 'Minister of Finance',
                'introduced_by_party': 'BJP',
                'ministry': 'Ministry of Finance',
                'description': 'A bill to give effect to the financial proposals of the Central Government for the financial year 2024-2025.',
                'objective': 'To implement the budget proposals and impose taxes for the financial year.',
                'loksabha_link': 'https://loksabha.nic.in/bills/finance-bill-2024',
                'source': 'LOK_SABHA',
                'tags': ['finance', 'budget', 'tax']
            },
            {
                'bill_id': 'LS-102',
                'bill_number': 'Bill No. 102 of 2024',
                'title': 'The Anti-Maritime Piracy Bill, 2024',
                'house': 'LOK_SABHA',
                'status': 'PENDING',
                'introduction_date': date.today() - timedelta(days=20),
                'introduced_by': 'Minister of External Affairs',
                'introduced_by_party': 'BJP',
                'ministry': 'Ministry of External Affairs',
                'description': 'A bill to give effect to the United Nations Convention on the Law of the Sea and combat maritime piracy.',
                'objective': 'To provide for punishment of maritime piracy and enhance maritime security.',
                'loksabha_link': 'https://loksabha.nic.in/bills/anti-piracy-bill-2024',
                'source': 'LOK_SABHA',
                'tags': ['maritime', 'piracy', 'security']
            }
        ]
        
        # Rajya Sabha Bills
        rs_bills = [
            {
                'bill_id': 'RS-201',
                'bill_number': 'RS Bill 201 of 2024',
                'title': 'The Coastal Shipping Bill, 2024',
                'house': 'RAJYA_SABHA',
                'status': 'PENDING',
                'introduction_date': date.today() - timedelta(days=25),
                'introduced_by': 'Minister of Ports and Shipping',
                'introduced_by_party': 'BJP',
                'ministry': 'Ministry of Ports and Shipping',
                'description': 'A bill to promote coastal shipping and enhance the efficiency of coastal trade.',
                'objective': 'To develop coastal shipping as an eco-friendly and economical mode of transport.',
                'rajyasabha_link': 'https://rajyasabha.nic.in/bills/coastal-shipping-bill-2024',
                'source': 'RAJYA_SABHA',
                'tags': ['shipping', 'transport', 'coastal']
            },
            {
                'bill_id': 'RS-202',
                'bill_number': 'RS Bill 202 of 2024',
                'title': 'The Disaster Management (Amendment) Bill, 2024',
                'house': 'RAJYA_SABHA',
                'status': 'PASSED',
                'introduction_date': date.today() - timedelta(days=80),
                'passed_date': date.today() - timedelta(days=15),
                'introduced_by': 'Minister of Home Affairs',
                'introduced_by_party': 'BJP',
                'ministry': 'Ministry of Home Affairs',
                'description': 'A bill to amend the Disaster Management Act to strengthen disaster response mechanisms.',
                'objective': 'To improve coordination and effectiveness in disaster management.',
                'rajyasabha_link': 'https://rajyasabha.nic.in/bills/disaster-management-amendment-bill-2024',
                'source': 'RAJYA_SABHA',
                'tags': ['disaster', 'management', 'safety']
            }
        ]
        
        # Add more bills with random dates
        for i in range(1, 11):
            days_ago = random.randint(1, 365)
            bills.append({
                'bill_id': f"BILL-2024-{str(i).zfill(3)}",
                'bill_number': f"Bill No. {i} of 2024",
                'title': f"The {random.choice(['Digital', 'Education', 'Health', 'Finance', 'Defense', 'Agriculture', 'Energy'])} Reform Bill, 2024",
                'house': random.choice(['LOK_SABHA', 'RAJYA_SABHA']),
                'status': random.choice(['PASSED', 'PENDING', 'REJECTED', 'WITHDRAWN']),
                'introduction_date': date.today() - timedelta(days=days_ago),
                'introduced_by': f"Minister of {random.choice(['Finance', 'Home Affairs', 'Defense', 'Education', 'Health'])}",
                'introduced_by_party': random.choice(['BJP', 'INC', 'Other']),
                'ministry': f"Ministry of {random.choice(['Finance', 'Home Affairs', 'Defense', 'Education', 'Health'])}",
                'description': f"This bill aims to reform the {random.choice(['digital', 'education', 'health', 'finance'])} sector.",
                'objective': f"To improve efficiency and transparency in {random.choice(['digital', 'education', 'health', 'finance'])}.",
                'source': random.choice(['PRS', 'LOK_SABHA', 'RAJYA_SABHA']),
                'tags': [random.choice(['reform', 'development', 'policy'])]
            })
        
        return prs_bills + ls_bills + rs_bills + bills
# tracker/management/commands/autoscrape.py
from django.core.management.base import BaseCommand
from tracker.scraper import RealBillScraper
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Auto-scrape real bills from official sources'
    
    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=3600,
                          help='Scraping interval in seconds')
        parser.add_argument('--once', action='store_true',
                          help='Run once and exit')
        parser.add_argument('--source', type=str, default='all',
                          choices=['all', 'mpa', 'prs', 'mock'],
                          help='Source to scrape from')
    
    def handle(self, *args, **options):
        interval = options['interval']
        once = options['once']
        source = options['source']
        
        scraper = RealBillScraper()
        
        self.stdout.write(self.style.SUCCESS(
            f"Auto-scraper started (source: {source}, interval: {interval}s)"
        ))
        
        while True:
            try:
                if source == 'all':
                    results = scraper.scrape_all()
                elif source == 'mpa':
                    bills = scraper.scrape_mpa_bills()
                    results = {'created': len(bills), 'updated': 0, 'failed': 0}
                    for bill in bills:
                        scraper._save_bill(bill)
                elif source == 'prs':
                    bills = scraper.scrape_prs_bills()
                    results = {'created': len(bills), 'updated': 0, 'failed': 0}
                    for bill in bills:
                        scraper._save_bill(bill)
                else:
                    from .autoscrape_mock import Command as MockCommand
                    mock_cmd = MockCommand()
                    results = mock_cmd.generate_mock_data()
                
                self.stdout.write(self.style.SUCCESS(
                    f"Scrape complete: {results}"
                ))
                
                if once:
                    break
                
                self.stdout.write(f"Waiting {interval} seconds...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\nStopped by user"))
                break