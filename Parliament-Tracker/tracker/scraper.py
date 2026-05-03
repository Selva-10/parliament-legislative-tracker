# tracker/scraper.py
import cloudscraper
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from django.utils import timezone
from .models import Bill
import re
import time
import hashlib

logger = logging.getLogger(__name__)

class RealBillScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False,
                'custom': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        logger.info("Bill scraper initialized")

    def _parse_date(self, date_str):
        """
        Parse date from DD/MM/YYYY format (MPA format)
        Returns date object or None
        """
        if not date_str or date_str.strip() == '':
            return None
        
        date_str = str(date_str).strip()
        
        # Skip if it's a dash or empty
        if date_str in ['-', '—', 'NA', 'N/A', '']:
            return None
        
        # Try DD/MM/YYYY format (MPA standard format)
        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
        if date_match:
            try:
                day, month, year = date_match.groups()
                parsed_date = datetime(int(year), int(month), int(day)).date()
                # Validate year is reasonable (2000-2030)
                if 2000 <= parsed_date.year <= 2030:
                    return parsed_date
            except ValueError:
                pass
        
        # Try alternative formats as fallback
        alt_formats = [
            '%d-%m-%Y',  # 16-04-2026
            '%d/%m/%Y',  # 16/04/2026
            '%Y-%m-%d',  # 2026-04-16
        ]
        
        for fmt in alt_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                if 2000 <= parsed_date.year <= 2030:
                    return parsed_date
            except ValueError:
                continue
        
        logger.debug(f"Could not parse date: {date_str}")
        return None

    def scrape_mpa_bills(self):
        """
        Scrape ALL MPA bills - NO STATUS CALCULATION
        Status will be updated by PRS status updater
        House defaults to LOK_SABHA
        """
        logger.info("=" * 60)
        logger.info("Scraping MPA Bills - Raw Data Only")
        logger.info("Status will be updated by PRS status updater")
        logger.info("=" * 60)
        
        bills = []
        base_url = "https://mpa.gov.in/bills-list"
        
        try:
            response = self.scraper.get(base_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"Failed to fetch MPA page: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            
            if not table:
                logger.warning("No table found on MPA page")
                return []
            
            rows = table.find_all('tr')
            total_rows = len(rows) - 1
            logger.info(f"Found {total_rows} total bills in MPA table")
            
            valid_count = 0
            skipped_count = 0
            
            for idx, row in enumerate(rows[1:], 1):
                try:
                    cols = row.find_all('td')
                    
                    # MPA has 6 columns
                    if len(cols) < 4:
                        logger.debug(f"Row {idx}: Only {len(cols)} columns, skipping")
                        skipped_count += 1
                        continue
                    
                    # Extract data from columns
                    title = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                    ministry = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                    
                    # Introduction date (Column 3)
                    intro_date_str = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                    intro_date = self._parse_date(intro_date_str)
                    
                    # Passed in Lok Sabha (Column 4)
                    passed_ls_str = cols[4].get_text(strip=True) if len(cols) > 4 else ''
                    passed_ls_date = self._parse_date(passed_ls_str) if passed_ls_str else None
                    
                    # Passed in Rajya Sabha (Column 5)
                    passed_rs_str = cols[5].get_text(strip=True) if len(cols) > 5 else ''
                    passed_rs_date = self._parse_date(passed_rs_str) if passed_rs_str else None
                    
                    if not title:
                        logger.debug(f"Row {idx}: No title found")
                        skipped_count += 1
                        continue
                    
                    if not intro_date:
                        logger.debug(f"Row {idx}: No valid introduction date for '{title[:40]}'")
                        skipped_count += 1
                        continue
                    
                    # Generate consistent bill_id from title
                    bill_id = f"MPA-{hashlib.md5(title.encode()).hexdigest()[:8].upper()}"
                    
                    # NO STATUS CALCULATION HERE
                    # Status will be updated by PRS status updater
                    # Default to 'PENDING' until PRS updates it
                    
                    bill_data = {
                        'bill_id': bill_id,
                        'bill_number': str(idx),
                        'title': title,
                        'introduction_date': intro_date,
                        'passed_in_ls_date': passed_ls_date,
                        'passed_in_rs_date': passed_rs_date,
                        'ministry': ministry,
                        'source': 'MPA',
                        'house': 'LOK_SABHA',  # Default, will be updated by PRS house updater
                        'status': 'PENDING',   # Default, will be updated by PRS status updater
                    }
                    
                    bills.append(bill_data)
                    valid_count += 1
                    
                    if valid_count % 20 == 0:
                        logger.info(f"  Processed {valid_count} bills...")
                    
                except Exception as e:
                    logger.error(f"Error on row {idx}: {e}")
                    skipped_count += 1
                    continue
            
            logger.info(f"\nMPA Scraping Summary:")
            logger.info(f"  Total bills scraped: {valid_count}")
            logger.info(f"  Skipped: {skipped_count}")
            logger.info(f"  Bills with LS passed date: {sum(1 for b in bills if b['passed_in_ls_date'])}")
            logger.info(f"  Bills with RS passed date: {sum(1 for b in bills if b['passed_in_rs_date'])}")
            logger.info(f"  Status set to: PENDING (will be updated by PRS)")
            logger.info(f"  House set to: LOK_SABHA (will be updated by PRS)")
            
            return bills
            
        except Exception as e:
            logger.error(f"MPA scrape error: {e}")
            return []

    def save_bills_to_db(self, bills):
        """Save scraped bills to database without duplicates"""
        from .models import Bill
        
        saved_count = 0
        updated_count = 0
        
        for bill_data in bills:
            try:
                obj, created = Bill.objects.update_or_create(
                    bill_id=bill_data.get('bill_id'),
                    defaults={
                        'title': bill_data.get('title', ''),
                        'bill_number': bill_data.get('bill_number', ''),
                        'introduction_date': bill_data.get('introduction_date'),
                        'passed_in_ls_date': bill_data.get('passed_in_ls_date'),
                        'passed_in_rs_date': bill_data.get('passed_in_rs_date'),
                        'ministry': bill_data.get('ministry', ''),
                        'source': 'MPA',
                        'house': 'LOK_SABHA',  # Default, will be updated by PRS house updater
                        'status': 'PENDING',   # Default, will be updated by PRS status updater
                        'last_updated': timezone.now(),
                    }
                )
                
                if created:
                    saved_count += 1
                else:
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Save error: {e}")
        
        logger.info(f"Saved: {saved_count} new, Updated: {updated_count} existing")
        logger.info("NOTE: Status and House are set to defaults. Run PRS updaters to correct them.")
        return saved_count + updated_count

    def scrape_and_save(self):
        """Main method to scrape and save MPA bills"""
        bills = self.scrape_mpa_bills()
        
        if not bills:
            logger.warning("No bills scraped")
            return 0
        
        return self.save_bills_to_db(bills)


# Helper function for management command
def scrape_mpa_bills():
    scraper = RealBillScraper()
    return scraper.scrape_and_save()