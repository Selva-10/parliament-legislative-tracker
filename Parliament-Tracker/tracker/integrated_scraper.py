# tracker/integrated_scraper.py
import cloudscraper
import logging
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime
from django.utils import timezone
from .models import Bill

logger = logging.getLogger(__name__)

class IntegratedBillScraper:
    """
    Integrated scraper that combines MPA data with PRS session house information
    """
    
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        # Cache for PRS session house data
        self.prs_house_cache = {}
        
    # Complete list of all PRS session URLs
    PRS_SESSION_URLS = [
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
    
    def load_prs_house_data(self):
        """Load all house data from PRS sessions into cache"""
        logger.info("Loading PRS session house data into cache...")
        
        for url in self.PRS_SESSION_URLS:
            try:
                response = self.scraper.get(url, timeout=30)
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find tables
                tables = soup.find_all('table')
                
                for table in tables:
                    # Check for House of Introduction column
                    header_row = table.find('tr')
                    if header_row:
                        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                        
                        if any('House of Introduction' in h for h in headers):
                            rows = table.find_all('tr')[1:]
                            
                            for row in rows:
                                cols = row.find_all('td')
                                if len(cols) >= 2:
                                    title = cols[0].get_text(strip=True)
                                    house_text = cols[1].get_text(strip=True)
                                    
                                    if title and house_text:
                                        # Clean title for matching
                                        clean_title = self.clean_title(title)
                                        
                                        # Convert to DB format
                                        if 'Lok Sabha' in house_text:
                                            db_house = 'LOK_SABHA'
                                        elif 'Rajya Sabha' in house_text:
                                            db_house = 'RAJYA_SABHA'
                                        else:
                                            db_house = 'LOK_SABHA'
                                        
                                        self.prs_house_cache[clean_title] = db_house
                                        
                time.sleep(0.5)  # Be respectful
                
            except Exception as e:
                logger.error(f"Error loading PRS data from {url}: {e}")
        
        logger.info(f"Loaded {len(self.prs_house_cache)} bill-house mappings from PRS sessions")
    
    def clean_title(self, title):
        """Clean bill title for matching"""
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title)
        # Remove [bracketed content]
        title = re.sub(r'\s*\[.*?\]\s*', ' ', title)
        # Remove extra spaces again
        title = re.sub(r'\s+', ' ', title)
        return title.strip()
    
    def get_house_from_prs(self, bill_title):
        """Get house of introduction from cached PRS data"""
        clean_title = self.clean_title(bill_title)
        
        # Try exact match
        if clean_title in self.prs_house_cache:
            return self.prs_house_cache[clean_title]
        
        # Try partial match (first 50 chars)
        short_title = clean_title[:50]
        for cached_title, house in self.prs_house_cache.items():
            if cached_title.startswith(short_title) or short_title in cached_title:
                return house
        
        # Try without year
        without_year = re.sub(r'\s*\d{4}\s*', ' ', clean_title)
        without_year = re.sub(r'\s+', ' ', without_year).strip()
        for cached_title, house in self.prs_house_cache.items():
            if without_year in cached_title or cached_title in without_year:
                return house
        
        return None  # Not found in PRS data
    
    def scrape_mpa_bills_with_prs_house(self):
        """Scrape MPA bills and enhance with PRS house data"""
        from .scraper import RealBillScraper
        
        logger.info("=" * 60)
        logger.info("Scraping MPA Bills with PRS House Enhancement")
        logger.info("=" * 60)
        
        # First, load PRS house data
        self.load_prs_house_data()
        
        # Scrape MPA bills
        mpa_scraper = RealBillScraper()
        mpa_bills = mpa_scraper.scrape_mpa_bills()
        
        if not mpa_bills:
            logger.warning("No MPA bills scraped")
            return []
        
        # Enhance with PRS house data
        enhanced_bills = []
        prs_found = 0
        
        for bill in mpa_bills:
            title = bill.get('title', '')
            
            # Try to get house from PRS data
            prs_house = self.get_house_from_prs(title)
            
            if prs_house:
                # Override the house with PRS data (more accurate)
                bill['house'] = prs_house
                prs_found += 1
                logger.debug(f"PRS house found: {title[:50]} → {prs_house}")
            else:
                # Keep original house calculation from MPA
                logger.debug(f"No PRS house: {title[:50]} → using MPA calculated house: {bill.get('house')}")
            
            enhanced_bills.append(bill)
        
        logger.info(f"PRS house data applied to {prs_found} out of {len(mpa_bills)} bills")
        
        return enhanced_bills
    
    def scrape_all(self):
        """Main scraping method with PRS house integration"""
        logger.info("=" * 60)
        logger.info("INTEGRATED BILL SCRAPER (MPA + PRS House Data)")
        logger.info("=" * 60)
        
        # Scrape MPA bills with PRS house enhancement
        bills = self.scrape_mpa_bills_with_prs_house()
        
        if not bills:
            logger.warning("No bills fetched")
            return {'created': 0, 'updated': 0, 'failed': 0}
        
        # Save to database
        results = {'created': 0, 'updated': 0, 'failed': 0}
        
        for bill_data in bills:
            try:
                obj, created = Bill.objects.update_or_create(
                    bill_id=bill_data.get('bill_id'),
                    defaults={
                        'bill_number': bill_data.get('bill_number', ''),
                        'title': bill_data.get('title', ''),
                        'house': bill_data.get('house', 'LOK_SABHA'),
                        'status': bill_data.get('status', 'PENDING'),
                        'introduction_date': bill_data.get('introduction_date'),
                        'passed_in_ls_date': bill_data.get('passed_in_ls_date'),
                        'passed_in_rs_date': bill_data.get('passed_in_rs_date'),
                        'ministry': bill_data.get('ministry', ''),
                        'source': 'MPA_WITH_PRS',
                        'last_updated': timezone.now(),
                    }
                )
                
                if created:
                    results['created'] += 1
                else:
                    results['updated'] += 1
                    
            except Exception as e:
                logger.error(f"Save error: {e}")
                results['failed'] += 1
        
        # Show final distribution
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING RESULTS WITH PRS HOUSE DATA:")
        logger.info(f"  Created: {results['created']}")
        logger.info(f"  Updated: {results['updated']}")
        logger.info(f"  Failed: {results['failed']}")
        logger.info("\n🏛️ HOUSE DISTRIBUTION IN DATABASE:")
        logger.info(f"  Lok Sabha: {Bill.objects.filter(house='LOK_SABHA').count()}")
        logger.info(f"  Rajya Sabha: {Bill.objects.filter(house='RAJYA_SABHA').count()}")
        logger.info(f"  Both: {Bill.objects.filter(house='BOTH').count()}")
        logger.info("=" * 60)
        
        return results


def integrated_scrape():
    """Run the integrated scraper"""
    scraper = IntegratedBillScraper()
    return scraper.scrape_all()