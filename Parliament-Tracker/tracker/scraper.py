# tracker/scraper.py
import cloudscraper
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from django.utils import timezone
from .models import Bill
import re
import time

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
        Scrape ALL MPA bills with ALL 6 columns including LS/RS passed dates
        """
        logger.info("=" * 60)
        logger.info("Scraping MPA Bills - COMPLETE DATA (6 Columns)")
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
            total_rows = len(rows) - 1  # Subtract header row
            logger.info(f"Found {total_rows} total bills in MPA table")
            
            # Get headers for debugging
            header_row = rows[0] if rows else None
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                logger.info(f"Table columns: {headers}")
            
            valid_count = 0
            skipped_count = 0
            passed_ls_count = 0
            passed_rs_count = 0
            passed_both_count = 0
            
            # Process each data row (skip header row)
            for idx, row in enumerate(rows[1:], 1):
                try:
                    cols = row.find_all('td')
                    
                    # MPA has 6 columns:
                    # Col 0: S.No
                    # Col 1: Title of the Bill
                    # Col 2: Ministry/Department
                    # Col 3: Introduced in LS/RS (Introduction Date)
                    # Col 4: Passed in LS (Lok Sabha passed date)
                    # Col 5: Passed in RS (Rajya Sabha passed date)
                    
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
                    
                    # Count bills with passed dates
                    if passed_ls_date:
                        passed_ls_count += 1
                    if passed_rs_date:
                        passed_rs_count += 1
                    if passed_ls_date and passed_rs_date:
                        passed_both_count += 1
                    
                    # Determine status based on passed dates
                    if passed_ls_date and passed_rs_date:
                        status = 'PASSED'
                        house = 'BOTH'
                    elif passed_ls_date:
                        status = 'PASSED'
                        house = 'LOK_SABHA'
                    elif passed_rs_date:
                        status = 'PASSED'
                        house = 'RAJYA_SABHA'
                    else:
                        status = 'PENDING'
                        house = 'LOK_SABHA'
                    
                    # Generate unique bill ID using index
                    bill_id = f"MPA-{idx:04d}"
                    
                    bill_data = {
                        'bill_id': bill_id,
                        'bill_number': str(idx),
                        'title': title,
                        'introduction_date': intro_date,
                        'passed_in_ls_date': passed_ls_date,
                        'passed_in_rs_date': passed_rs_date,
                        'ministry': ministry,
                        'source': 'MPA',
                        'house': house,
                        'status': status,
                        'introduced_by': '',
                        'introduced_by_party': '',
                        'description': '',
                        'prs_link': '',
                    }
                    
                    bills.append(bill_data)
                    valid_count += 1
                    
                    # Log progress for bills with passed dates
                    if passed_ls_date or passed_rs_date:
                        logger.info(f"  ✓ [{idx}] {title[:40]} | Intro: {intro_date} | LS: {passed_ls_date} | RS: {passed_rs_date}")
                    elif valid_count % 20 == 0:
                        logger.info(f"  ✓ Processed {valid_count} bills...")
                    
                except Exception as e:
                    logger.error(f"Error on row {idx}: {e}")
                    skipped_count += 1
                    continue
            
            logger.info(f"\n📊 MPA Scraping Summary:")
            logger.info(f"  ✓ Bills with valid dates: {valid_count}")
            logger.info(f"  ✗ Skipped (no valid date): {skipped_count}")
            logger.info(f"\n📅 Passed Dates Summary:")
            logger.info(f"  ✓ Passed in Lok Sabha: {passed_ls_count}")
            logger.info(f"  ✓ Passed in Rajya Sabha: {passed_rs_count}")
            logger.info(f"  ✓ Passed in Both Houses: {passed_both_count}")
            
            return bills
            
        except Exception as e:
            logger.error(f"MPA scrape error: {e}")
            return []

    def scrape_all(self):
        """
        Main scraping method - saves ALL MPA bills with ALL columns
        """
        logger.info("=" * 60)
        logger.info("STARTING COMPLETE BILL SCRAPER")
        logger.info("=" * 60)
        
        all_bills = self.scrape_mpa_bills()
        
        if not all_bills:
            logger.warning("No bills fetched from MPA")
            return {'created': 0, 'updated': 0, 'failed': 0}
        
        results = {'created': 0, 'updated': 0, 'failed': 0}
        
        for bill_data in all_bills:
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
                        'introduced_by': bill_data.get('introduced_by', ''),
                        'introduced_by_party': bill_data.get('introduced_by_party', ''),
                        'description': bill_data.get('description', ''),
                        'source': bill_data.get('source', 'MPA'),
                        'prs_link': bill_data.get('prs_link', ''),
                        'last_updated': timezone.now(),
                    }
                )
                
                if created:
                    results['created'] += 1
                else:
                    results['updated'] += 1
                    
            except Exception as e:
                logger.error(f"Save error for {bill_data.get('bill_id')}: {e}")
                results['failed'] += 1
        
        # Final statistics
        total = Bill.objects.count()
        with_ls = Bill.objects.filter(passed_in_ls_date__isnull=False).count()
        with_rs = Bill.objects.filter(passed_in_rs_date__isnull=False).count()
        with_both = Bill.objects.filter(passed_in_ls_date__isnull=False, passed_in_rs_date__isnull=False).count()
        
        logger.info("=" * 60)
        logger.info("FINAL SCRAPING RESULTS:")
        logger.info(f"  - Total bills in DB: {total}")
        logger.info(f"  - Newly created: {results['created']}")
        logger.info(f"  - Updated: {results['updated']}")
        logger.info(f"  - Failed: {results['failed']}")
        logger.info(f"  - Passed in Lok Sabha: {with_ls}")
        logger.info(f"  - Passed in Rajya Sabha: {with_rs}")
        logger.info(f"  - Passed in Both Houses: {with_both}")
        logger.info("=" * 60)
        
        return results