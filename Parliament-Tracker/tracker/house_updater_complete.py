# tracker/house_updater_complete.py
import cloudscraper
import logging
import re
import time
from bs4 import BeautifulSoup
from django.utils import timezone
from django.db import transaction
from .models import Bill

logger = logging.getLogger(__name__)

class PRSCompleteHouseUpdater:
    """Complete scraper for all PRS sessions to update house column"""
    
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
    # Complete list of all session URLs from 2019-2026
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
        # Remove bracketed content like [Delimitation Bills of 2026]
        title = re.sub(r'\s*\[.*?\]\s*', ' ', title)
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title)
        return title.strip()
    
    def scrape_session_houses(self, url):
        """Scrape House of Introduction from a session page"""
        try:
            response = self.scraper.get(url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            house_data = {}
            
            # Find the "New Bills Introduced" table
            # Look for the table that contains "House of Introduction" header
            tables = soup.find_all('table')
            
            for table in tables:
                # Check if this table has House of Introduction column
                header_row = table.find('tr')
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                    
                    # Look for the correct table
                    if 'House of Introduction' in headers or ('Title' in headers and 'House of Introduction' in str(headers)):
                        rows = table.find_all('tr')[1:]  # Skip header row
                        
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                title = cols[0].get_text(strip=True)
                                house_text = cols[1].get_text(strip=True)
                                
                                if title and house_text and len(title) > 10:
                                    # Determine house
                                    if 'Lok Sabha' in house_text:
                                        db_house = 'LOK_SABHA'
                                    elif 'Rajya Sabha' in house_text:
                                        db_house = 'RAJYA_SABHA'
                                    else:
                                        db_house = 'LOK_SABHA'
                                    
                                    clean_title = self.clean_title(title)
                                    house_data[clean_title] = db_house
                        
                        # Found the right table, break out
                        if house_data:
                            break
            
            return house_data
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {}
    
    def scrape_all_houses(self):
        """Scrape house information from all session URLs"""
        all_house_data = {}
        
        for i, url in enumerate(self.SESSION_URLS, 1):
            session_name = url.split('/')[-2]
            print(f"  [{i}/{len(self.SESSION_URLS)}] Scraping {session_name}...")
            
            house_data = self.scrape_session_houses(url)
            all_house_data.update(house_data)
            
            if house_data:
                print(f"      Found {len(house_data)} bills with house info")
            
            time.sleep(1)  # Be respectful
        
        print(f"\n Total unique bills with house info: {len(all_house_data)}")
        return all_house_data
    
    def update_bill_house(self, scraped_title, house):
        """Find matching bill and update house field"""
        clean_scraped = self.clean_title(scraped_title)
        
        # Try multiple matching strategies
        # Strategy 1: Exact match on cleaned title
        matches = Bill.objects.filter(source='MPA', title__iexact=scraped_title)
        
        # Strategy 2: Title contains the scraped title
        if not matches.exists():
            matches = Bill.objects.filter(source='MPA', title__icontains=clean_scraped[:60])
        
        # Strategy 3: Remove "The" and try
        if not matches.exists():
            without_the = re.sub(r'^The\s+', '', clean_scraped)
            if without_the != clean_scraped:
                matches = Bill.objects.filter(source='MPA', title__icontains=without_the[:60])
        
        if matches.exists():
            updated = 0
            for bill in matches:
                if bill.house != house:
                    old_house = bill.house
                    bill.house = house
                    bill.save()
                    updated += 1
                    print(f"      Updated: {scraped_title[:50]}... | {old_house} -> {house}")
                else:
                    print(f"      Already correct: {scraped_title[:50]}... -> {house}")
            return updated
        
        print(f"      No match found for: {scraped_title[:50]}...")
        return 0
    
    def update_all_houses(self, house_data):
        """Update all matched bills with house information"""
        updated_count = 0
        matched_count = 0
        
        for title, house in house_data.items():
            updated = self.update_bill_house(title, house)
            if updated > 0:
                updated_count += updated
                matched_count += 1
        
        return updated_count, matched_count
    
    def scrape_and_update_all(self):
        """Main method to scrape all sessions and update house data"""
        print("=" * 70)
        print("PRS HOUSE UPDATER - All Sessions (2019-2026)")
        print("=" * 70)
        print(f"Total sessions to scrape: {len(self.SESSION_URLS)}")
        
        # Count MPA bills
        mpa_count = Bill.objects.filter(source='MPA').count()
        print(f"Total MPA bills in database: {mpa_count}")
        print("=" * 70)
        
        # Scrape house data from all sessions
        print("\nScraping house information from PRS sessions...")
        house_data = self.scrape_all_houses()
        
        if not house_data:
            print("No house data scraped from PRS")
            return {'bills_scraped': 0, 'bills_updated': 0}
        
        # Update database
        print("\nUpdating MPA bills with house information...")
        updated_count, matched_count = self.update_all_houses(house_data)
        
        print("\n" + "=" * 70)
        print("HOUSE UPDATE SUMMARY")
        print("=" * 70)
        print(f"  House entries scraped: {len(house_data)}")
        print(f"  Bills matched: {matched_count}")
        print(f"  Bills updated: {updated_count}")
        
        # Show final house distribution
        print("\nFINAL HOUSE DISTRIBUTION:")
        print(f"  Lok Sabha: {Bill.objects.filter(source='MPA', house='LOK_SABHA').count()}")
        print(f"  Rajya Sabha: {Bill.objects.filter(source='MPA', house='RAJYA_SABHA').count()}")
        print(f"  PENDING: {Bill.objects.filter(source='MPA', house='PENDING').count()}")
        print("=" * 70)
        
        return {'bills_scraped': len(house_data), 'bills_updated': updated_count}


def update_all_houses():
    updater = PRSCompleteHouseUpdater()
    return updater.scrape_and_update_all()
# Add at the bottom of house_updater_complete.py

if __name__ == "__main__":
    import os
    import sys
    import django
    
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parliment.settings')
    django.setup()
    
    from tracker.models import Bill
    
    updater = PRSCompleteHouseUpdater()
    result = updater.scrape_and_update_all()
    print(result)