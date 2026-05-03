# tracker/prs_status_updater.py
import cloudscraper
import logging
import re
from bs4 import BeautifulSoup
from django.utils import timezone
from django.db import transaction
from .models import Bill

logger = logging.getLogger(__name__)

class PRSStatusUpdater:
    """
    Status updater for MPA bills using year-wise PRS URLs.
    This OVERRIDES the status calculated by scraper.py with PRS status.
    """
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

    # Map PRS status text to database status
    STATUS_MAPPING = {
        'Passed': 'PASSED',
        'Passed by Both Houses': 'PASSED',
        'Passed by LS': 'PASSED',
        'Passed by RS': 'PASSED',
        'Pending': 'PENDING',
        'In Committee': 'PENDING',
        'Introduced': 'PENDING',
        'Withdrawn': 'WITHDRAWN',
        'Lapsed': 'LAPSED',
        'Negatived': 'REJECTED',
        'Introduced-Negatived': 'REJECTED',
        'Introduced - Infructuous': 'LAPSED',
        'Draft': 'PENDING',
        'Replaced by an Act': 'PASSED',
    }

    YEAR_URLS = {
        '2019': 'https://prsindia.org/billtrack/category/all?BillActsBillsParliamentSearch%5Btitle%5D=&BillActsBillsParliamentSearch%5Bbill_status_id%5D=&BillActsBillsParliamentSearch%5Bdate_of_introduction%5D=2019',
        '2020': 'https://prsindia.org/billtrack/category/all?BillActsBillsParliamentSearch%5Btitle%5D=&BillActsBillsParliamentSearch%5Bbill_status_id%5D=&BillActsBillsParliamentSearch%5Bdate_of_introduction%5D=2020',
        '2021': 'https://prsindia.org/billtrack/category/all?BillActsBillsParliamentSearch%5Btitle%5D=&BillActsBillsParliamentSearch%5Bbill_status_id%5D=&BillActsBillsParliamentSearch%5Bdate_of_introduction%5D=2021',
        '2022': 'https://prsindia.org/billtrack/category/all?BillActsBillsParliamentSearch%5Btitle%5D=&BillActsBillsParliamentSearch%5Bbill_status_id%5D=&BillActsBillsParliamentSearch%5Bdate_of_introduction%5D=2022',
        '2023': 'https://prsindia.org/billtrack/category/all?BillActsBillsParliamentSearch%5Btitle%5D=&BillActsBillsParliamentSearch%5Bbill_status_id%5D=&BillActsBillsParliamentSearch%5Bdate_of_introduction%5D=2023',
        '2024': 'https://prsindia.org/billtrack/category/all?BillActsBillsParliamentSearch%5Btitle%5D=&BillActsBillsParliamentSearch%5Bbill_status_id%5D=&BillActsBillsParliamentSearch%5Bdate_of_introduction%5D=2024',
        '2025': 'https://prsindia.org/billtrack/category/all?BillActsBillsParliamentSearch%5Btitle%5D=&BillActsBillsParliamentSearch%5Bbill_status_id%5D=&BillActsBillsParliamentSearch%5Bdate_of_introduction%5D=2025',
        '2026': 'https://prsindia.org/billtrack/category/all?BillActsBillsParliamentSearch%5Btitle%5D=&BillActsBillsParliamentSearch%5Bbill_status_id%5D=&BillActsBillsParliamentSearch%5Bdate_of_introduction%5D=2026',
    }

    def clean_title(self, title):
        """Clean bill title for matching."""
        title = re.sub(r'\s*\[.*?\]\s*', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        return title.strip()

    def scrape_year_statuses(self, year, url):
        """Scrape bills and statuses from a specific year URL."""
        print(f"  Scraping {year}...")
        
        try:
            response = self.scraper.get(url, timeout=30)
            if response.status_code != 200:
                print(f"    Failed: HTTP {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            statuses = {}
            
            # Get all text and split into lines
            text = soup.get_text()
            lines = text.split('\n')
            
            current_bill = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line contains a bill title
                if 'Bill' in line and len(line) < 200 and len(line) > 10:
                    skip_words = ['Search', 'Filter', 'FIND', 'Home', 'MPs', 'Parliament', 'States', 'Legislature', 'Budget', 'Acts']
                    if not any(skip in line for skip in skip_words):
                        current_bill = self.clean_title(line)
                
                # Check for status in the line
                if current_bill:
                    for prs_status, db_status in self.STATUS_MAPPING.items():
                        if prs_status.lower() in line.lower():
                            statuses[current_bill] = db_status
                            print(f"    Found: {current_bill[:50]}... -> {db_status}")
                            current_bill = None
                            break
            
            print(f"    Total: {len(statuses)} bills with status")
            return statuses
            
        except Exception as e:
            print(f"    Error: {e}")
            return {}

    def scrape_all_statuses(self):
        """Scrape statuses from all years."""
        all_statuses = {}
        
        for year, url in self.YEAR_URLS.items():
            year_statuses = self.scrape_year_statuses(year, url)
            all_statuses.update(year_statuses)
        
        print(f"\n Total unique statuses scraped: {len(all_statuses)}")
        return all_statuses

    def update_mpa_bills_with_prs_status(self, scraped_statuses):
        """
        UPDATE ALL MATCHED BILLS with PRS status.
        This OVERRIDES the status calculated by scraper.py.
        """
        mpa_bills = Bill.objects.filter(source='MPA')
        print(f"\n Found {mpa_bills.count()} MPA bills in database")
        
        # Create mapping of cleaned titles to bills
        bill_map = {}
        for bill in mpa_bills:
            bill_map[self.clean_title(bill.title)] = bill
        
        updated_count = 0
        matched_count = 0
        not_found_count = 0
        bills_to_update = []
        
        for prs_title, new_status in scraped_statuses.items():
            if prs_title in bill_map:
                matched_count += 1
                bill = bill_map[prs_title]
                old_status = bill.status
                
                # FORCE UPDATE - Always update with PRS status
                bill.status = new_status
                bills_to_update.append(bill)
                updated_count += 1
                
                if old_status != new_status:
                    print(f"  STATUS CHANGED: {prs_title[:50]}... | {old_status} -> {new_status}")
                else:
                    print(f"  Status confirmed (PRS): {prs_title[:50]}... -> {new_status}")
            else:
                not_found_count += 1
        
        # Bulk update all matched bills
        if bills_to_update:
            with transaction.atomic():
                for bill in bills_to_update:
                    bill.save()
        
        print(f"\n Results:")
        print(f"  Found in PRS: {matched_count} bills")
        print(f"  Not found in PRS: {not_found_count} bills")
        print(f"  Updated with PRS status: {updated_count} bills")
        
        return updated_count, matched_count

    def scrape_and_update_all(self):
        """Main method to scrape and update all statuses from PRS."""
        print("=" * 60)
        print("PRS STATUS UPDATER (Overrides scraper.py status)")
        print("=" * 60)
        
        # Step 1: Scrape statuses from all years
        scraped_statuses = self.scrape_all_statuses()
        
        if not scraped_statuses:
            print("No statuses scraped from PRS")
            return {'scraped': 0, 'updated': 0, 'matched': 0}
        
        # Step 2: Update MPA bills with PRS status (FORCE UPDATE)
        updated, matched = self.update_mpa_bills_with_prs_status(scraped_statuses)
        
        # Step 3: Show final distribution
        print("\n" + "=" * 60)
        print("FINAL STATUS DISTRIBUTION (After PRS Update)")
        print("=" * 60)
        print(f"  Passed: {Bill.objects.filter(source='MPA', status='PASSED').count()}")
        print(f"  Pending: {Bill.objects.filter(source='MPA', status='PENDING').count()}")
        print(f"  Rejected: {Bill.objects.filter(source='MPA', status='REJECTED').count()}")
        print(f"  Withdrawn: {Bill.objects.filter(source='MPA', status='WITHDRAWN').count()}")
        print(f"  Lapsed: {Bill.objects.filter(source='MPA', status='LAPSED').count()}")
        print("=" * 60)
        
        return {'scraped': len(scraped_statuses), 'updated': updated, 'matched': matched}


def update_statuses_from_prs():
    """Run the status updater."""
    updater = PRSStatusUpdater()
    return updater.scrape_and_update_all()