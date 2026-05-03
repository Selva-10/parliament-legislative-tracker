# tracker/state_scraper.py
import cloudscraper
import logging
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import Bill
import re
import time

logger = logging.getLogger(__name__)

class StateBillsScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        logger.info("State Bills Scraper initialized")
    
    def scrape_state_bills(self, state_name):
        """Scrape bills for a specific state from PRS India"""
        url = f"https://prsindia.org/bills/states?title=&state={state_name}&year=All"
        
        try:
            response = self.scraper.get(url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {state_name}: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            bills = []
            
            # Find bill items
            bill_items = soup.find_all('div', class_='views-row')
            
            for item in bill_items:
                link = item.find('a')
                if link:
                    title = link.get_text(strip=True)
                    if 'Bill' in title:
                        # Generate bill ID
                        bill_id = f"STATE-{state_name[:3].upper()}-{abs(hash(title)) % 1000:03d}"
                        
                        # Extract year from title
                        year_match = re.search(r'202[4-6]', title)
                        year = year_match.group() if year_match else '2026'
                        
                        bills.append({
                            'bill_id': bill_id,
                            'title': title,
                            'state': state_name,
                            'legislative_year': year,
                            'source': 'STATE_BILL',
                            'status': 'PENDING',
                            'introduction_date': None,
                        })
            
            logger.info(f"Found {len(bills)} bills for {state_name}")
            return bills
            
        except Exception as e:
            logger.error(f"Error scraping {state_name}: {e}")
            return []
    
    def scrape_all_states(self):
        """Scrape bills for all major Indian states"""
        states = [
            'Maharashtra', 'Tamil Nadu', 'Gujarat', 'Kerala', 'Punjab',
            'West Bengal', 'Rajasthan', 'Uttar Pradesh', 'Madhya Pradesh',
            'Bihar', 'Odisha', 'Telangana', 'Andhra Pradesh', 'Haryana', 'Delhi',
            'Karnataka', 'Assam', 'Jharkhand', 'Chhattisgarh', 'Goa'
        ]
        
        all_bills = []
        for state in states:
            bills = self.scrape_state_bills(state)
            all_bills.extend(bills)
            time.sleep(2)  # Respectful delay between states
        
        logger.info(f"Total state bills scraped: {len(all_bills)}")
        return all_bills
    
    def save_bills_to_db(self, bills):
        saved_count = 0
        for bill_data in bills:
        # Check if bill already exists
            existing = Bill.objects.filter(
                source='STATE_BILL',
                title=bill_data.get('title'),
                state=bill_data.get('state'),
                legislative_year=bill_data.get('legislative_year')
            ).first()
        
            if not existing:
                Bill.objects.create(**bill_data)
                saved_count += 1
            else:
            # Update existing instead of creating duplicate
                existing.title = bill_data.get('title')
                existing.save()
                saved_count += 1
    
        return saved_count


def scrape_all_state_bills():
    scraper = StateBillsScraper()
    bills = scraper.scrape_all_states()
    return scraper.save_bills_to_db(bills)