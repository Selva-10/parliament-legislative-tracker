# tracker/management/commands/update_all_houses.py
from django.core.management.base import BaseCommand
from datetime import datetime
import cloudscraper
import re
import time
from bs4 import BeautifulSoup
from tracker.models import Bill
from django.db import transaction

class Command(BaseCommand):
    help = 'Update house information from PRS session pages (2019-2026)'

    # All PRS session URLs
    SESSION_URLS = [
        "https://prsindia.org/sessiontrack/budget-session-2026/bill-legislation",
        "https://prsindia.org/sessiontrack/budget-session-2025/bill-legislation",
        "https://prsindia.org/sessiontrack/monsoon-session-2025/bill-legislation",
        "https://prsindia.org/sessiontrack/winter-session-2025/bill-legislation",
        "https://prsindia.org/sessiontrack/budget-session-2024-18th-ls/bill-legislation",
        "https://prsindia.org/sessiontrack/winter-session-2024/bill-legislation",
        "https://prsindia.org/sessiontrack/first-session-2024-18th-ls/bill-legislation",
        "https://prsindia.org/sessiontrack/budget-session-2023/bill-legislation",
        "https://prsindia.org/sessiontrack/monsoon-session-2023/bill-legislation",
        "https://prsindia.org/sessiontrack/special-session-2023/bill-legislation",
        "https://prsindia.org/sessiontrack/winter-session-2023/bill-legislation",
        "https://prsindia.org/sessiontrack/budget-session-2022/bill-legislation",
        "https://prsindia.org/sessiontrack/monsoon-session-2022/bill-legislation",
        "https://prsindia.org/sessiontrack/winter-session-2022/bill-legislation",
        "https://prsindia.org/sessiontrack/budget-session-2021/bill-legislation",
        "https://prsindia.org/sessiontrack/monsoon-session-2021/bill-legislation",
        "https://prsindia.org/sessiontrack/winter-session-2021/bill-legislation",
        "https://prsindia.org/sessiontrack/budget-session-2020/bill-legislation",
        "https://prsindia.org/sessiontrack/monsoon-session-2020/bill-legislation",
        "https://prsindia.org/sessiontrack/budget-session-2019-17th-ls/bill-legislation",
        "https://prsindia.org/sessiontrack/winter-session-2019/bill-legislation",
    ]

    def clean_title(self, title):
        """Clean bill title for matching"""
        title = re.sub(r'\s*\[.*?\]\s*', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        return title.strip()

    def scrape_session_houses(self, url):
        """Scrape House of Introduction from a session page"""
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        try:
            response = scraper.get(url, timeout=30)
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            house_data = {}
            
            tables = soup.find_all('table')
            
            for table in tables:
                header_row = table.find('tr')
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                    
                    if 'House of Introduction' in str(headers):
                        rows = table.find_all('tr')[1:]
                        
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                title = cols[0].get_text(strip=True)
                                house_text = cols[1].get_text(strip=True)
                                
                                if title and house_text and len(title) > 10:
                                    if 'Lok Sabha' in house_text:
                                        db_house = 'LOK_SABHA'
                                    elif 'Rajya Sabha' in house_text:
                                        db_house = 'RAJYA_SABHA'
                                    else:
                                        db_house = 'LOK_SABHA'
                                    
                                    clean_title = self.clean_title(title)
                                    house_data[clean_title] = db_house
                        
                        if house_data:
                            break
            
            return house_data
            
        except Exception as e:
            self.stdout.write(f"      Error: {e}")
            return {}

    def handle(self, *args, **options):
        self.stdout.write(f"\n Starting house update at {datetime.now()}")
        self.stdout.write("=" * 60)
        self.stdout.write("PRS HOUSE UPDATER - All Sessions (2019-2026)")
        self.stdout.write("=" * 60)
        
        all_house_data = {}
        
        # Scrape all sessions
        for i, url in enumerate(self.SESSION_URLS, 1):
            session_name = url.split('/')[-2]
            self.stdout.write(f"  [{i}/{len(self.SESSION_URLS)}] Scraping {session_name}...")
            
            house_data = self.scrape_session_houses(url)
            all_house_data.update(house_data)
            
            if house_data:
                self.stdout.write(f"      Found {len(house_data)} bills with house info")
            
            time.sleep(1)
        
        self.stdout.write(f"\n Total unique bills with house info: {len(all_house_data)}")
        
        # Update MPA bills
        self.stdout.write("\n Updating MPA bills with house information...")
        
        mpa_bills = Bill.objects.filter(source='MPA')
        self.stdout.write(f" Total MPA bills in database: {mpa_bills.count()}")
        
        updated_count = 0
        matched_count = 0
        
        for bill in mpa_bills:
            clean_bill_title = self.clean_title(bill.title)
            
            if clean_bill_title in all_house_data:
                matched_count += 1
                new_house = all_house_data[clean_bill_title]
                
                if bill.house != new_house:
                    old_house = bill.house
                    bill.house = new_house
                    bill.save()
                    updated_count += 1
                    self.stdout.write(f"      Updated: {bill.title[:50]}... | {old_house} -> {new_house}")
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("HOUSE UPDATE SUMMARY")
        self.stdout.write("=" * 60)
        self.stdout.write(f"  House entries scraped: {len(all_house_data)}")
        self.stdout.write(f"  Bills matched: {matched_count}")
        self.stdout.write(f"  Bills updated: {updated_count}")
        
        # Final distribution
        self.stdout.write("\n FINAL HOUSE DISTRIBUTION:")
        self.stdout.write(f"  Lok Sabha: {Bill.objects.filter(source='MPA', house='LOK_SABHA').count()}")
        self.stdout.write(f"  Rajya Sabha: {Bill.objects.filter(source='MPA', house='RAJYA_SABHA').count()}")
        self.stdout.write(f"  PENDING: {Bill.objects.filter(source='MPA', house='PENDING').count()}")
        self.stdout.write("=" * 60)
        
        self.stdout.write(self.style.SUCCESS(f"\n Complete! Updated {updated_count} bills"))