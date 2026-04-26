# tracker/sansad_scraper.py - Working version for Next.js site
import cloudscraper
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from django.utils import timezone
from .models import Bill
import re
import time
import json

logger = logging.getLogger(__name__)

class SansadBillScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False,
                'custom': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        logger.info("Sansad Bill Scraper initialized")

    def _parse_date(self, date_str):
        """Parse date from various formats"""
        if not date_str or date_str.strip() in ['', '-', '—', 'NA', 'N/A']:
            return None
        
        date_str = str(date_str).strip()
        
        # Try DD/MM/YYYY format
        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
        if date_match:
            try:
                day, month, year = date_match.groups()
                return datetime(int(year), int(month), int(day)).date()
            except ValueError:
                pass
        
        # Try DD-MM-YYYY format
        date_match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{4})', date_str)
        if date_match:
            try:
                day, month, year = date_match.groups()
                return datetime(int(year), int(month), int(day)).date()
            except ValueError:
                pass
        
        # Try YYYY-MM-DD format
        date_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if date_match:
            try:
                year, month, day = date_match.groups()
                return datetime(int(year), int(month), int(day)).date()
            except ValueError:
                pass
        
        return None

    def scrape_from_nextjs_data(self, house='ls'):
        """Extract bills data from Next.js embedded JSON"""
        logger.info(f"Scraping {house.upper()} bills from Next.js data")
        
        bills = []
        
        # Next.js page URL
        if house == 'ls':
            url = "https://sansad.in/ls/legislation/bills"
        else:
            url = "https://sansad.in/rs/legislation/bills"
        
        try:
            response = self.scraper.get(url, timeout=30)
            if response.status_code != 200:
                logger.error(f"Failed to fetch {url}: {response.status_code}")
                return []
            
            # Look for Next.js data in script tags
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find script tags with __NEXT_DATA__
            next_data_script = None
            for script in soup.find_all('script', id='__NEXT_DATA__'):
                next_data_script = script
                break
            
            if next_data_script:
                try:
                    data = json.loads(next_data_script.string)
                    logger.info("Found Next.js data")
                    
                    # Navigate through the Next.js data structure
                    # The actual bills data is usually in props.pageProps
                    if 'props' in data:
                        page_props = data['props']
                        
                        # Look for bills data in various possible locations
                        possible_paths = [
                            ['pageProps', 'bills'],
                            ['pageProps', 'data'],
                            ['pageProps', 'legislationData'],
                            ['pageProps', 'initialData'],
                        ]
                        
                        bills_data = None
                        for path in possible_paths:
                            temp = page_props
                            found = True
                            for key in path:
                                if isinstance(temp, dict) and key in temp:
                                    temp = temp[key]
                                else:
                                    found = False
                                    break
                            if found and isinstance(temp, (list, dict)):
                                bills_data = temp
                                logger.info(f"Found bills data at path: {' -> '.join(path)}")
                                break
                        
                        if bills_data:
                            # If it's a list of bills
                            if isinstance(bills_data, list):
                                for item in bills_data:
                                    bill = self._extract_bill_from_json(item, house)
                                    if bill:
                                        bills.append(bill)
                            # If it's a dict with a results key
                            elif isinstance(bills_data, dict):
                                for key in ['results', 'data', 'items', 'bills']:
                                    if key in bills_data and isinstance(bills_data[key], list):
                                        for item in bills_data[key]:
                                            bill = self._extract_bill_from_json(item, house)
                                            if bill:
                                                bills.append(bill)
                    
                    logger.info(f"Extracted {len(bills)} bills from Next.js data")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Next.js data: {e}")
            else:
                logger.warning("No __NEXT_DATA__ script found")
                
                # Alternative: Look for data in other script tags
                for script in soup.find_all('script'):
                    if script.string and 'bills' in script.string.lower():
                        # Try to extract JSON-like data
                        json_match = re.search(r'({.*"bills".*})', script.string, re.DOTALL)
                        if json_match:
                            try:
                                data = json.loads(json_match.group(1))
                                logger.info("Found bills data in script tag")
                                # Process data similarly
                            except:
                                pass
            
            return bills
            
        except Exception as e:
            logger.error(f"Error scraping Next.js data: {e}")
            return []

    def _extract_bill_from_json(self, item, house):
        """Extract bill data from JSON item"""
        try:
            # Try different possible field names
            title = (item.get('title') or 
                    item.get('shortTitle') or 
                    item.get('name') or 
                    item.get('billTitle') or
                    item.get('short_title'))
            
            if not title:
                return None
            
            # Extract dates
            intro_date = None
            passed_ls = None
            passed_rs = None
            
            # Try different date field names
            for date_field in ['introductionDate', 'date_introduction', 'introDate', 'dateIntroduced']:
                if date_field in item:
                    intro_date = self._parse_date(item[date_field])
                    if intro_date:
                        break
            
            for date_field in ['passedLsDate', 'passed_ls', 'lokSabhaPassDate', 'datePassedLS']:
                if date_field in item:
                    passed_ls = self._parse_date(item[date_field])
                    if passed_ls:
                        break
            
            for date_field in ['passedRsDate', 'passed_rs', 'rajyaSabhaPassDate', 'datePassedRS']:
                if date_field in item:
                    passed_rs = self._parse_date(item[date_field])
                    if passed_rs:
                        break
            
            # Extract ministry
            ministry = (item.get('ministry') or 
                       item.get('department') or 
                       item.get('ministryName') or '')
            
            # Extract member
            member = (item.get('member') or 
                     item.get('introducedBy') or 
                     item.get('sponsor') or '')
            
            # Determine status
            if passed_ls and passed_rs:
                status = 'PASSED'
            elif passed_ls or passed_rs:
                status = 'PASSED'
            else:
                status = 'PENDING'
            
            # Generate bill ID
            bill_id = f"SANSAD-{house.upper()}-{abs(hash(title)) % 10000:04d}"
            
            return {
                'bill_id': bill_id,
                'title': title[:500],
                'short_title': title[:200],
                'introduction_date': intro_date,
                'passed_in_ls_date': passed_ls,
                'passed_in_rs_date': passed_rs,
                'ministry': ministry[:200],
                'member_name': member[:200],
                'source': 'SANSAD_NEXTJS',
                'house': 'LOK_SABHA' if house == 'ls' else 'RAJYA_SABHA',
                'status': status,
            }
        except Exception as e:
            logger.error(f"Error extracting bill from JSON: {e}")
            return None

    def scrape_lok_sabha_bills(self):
        """Scrape Lok Sabha bills"""
        logger.info("=" * 60)
        logger.info("Scraping Lok Sabha Bills from Sansad.in")
        logger.info("=" * 60)
        return self.scrape_from_nextjs_data(house='ls')

    def scrape_rajya_sabha_bills(self):
        """Scrape Rajya Sabha bills"""
        logger.info("=" * 60)
        logger.info("Scraping Rajya Sabha Bills from Sansad.in")
        logger.info("=" * 60)
        return self.scrape_from_nextjs_data(house='rs')

    def scrape_all(self):
        """Main scraping method"""
        all_bills = []
        
        # Scrape Lok Sabha bills
        ls_bills = self.scrape_lok_sabha_bills()
        all_bills.extend(ls_bills)
        
        # Scrape Rajya Sabha bills
        rs_bills = self.scrape_rajya_sabha_bills()
        all_bills.extend(rs_bills)
        
        if not all_bills:
            logger.warning("No bills fetched from Sansad.in")
            return {'created': 0, 'updated': 0, 'failed': 0, 'message': 'No data found - website uses JavaScript'}
        
        # Save to database
        results = {'created': 0, 'updated': 0, 'failed': 0}
        
        for bill_data in all_bills:
            try:
                obj, created = Bill.objects.update_or_create(
                    bill_id=bill_data.get('bill_id'),
                    defaults={
                        'title': bill_data.get('title', ''),
                        'short_title': bill_data.get('short_title', ''),
                        'introduction_date': bill_data.get('introduction_date'),
                        'passed_in_ls_date': bill_data.get('passed_in_ls_date'),
                        'passed_in_rs_date': bill_data.get('passed_in_rs_date'),
                        'ministry': bill_data.get('ministry', ''),
                        'member_name': bill_data.get('member_name', ''),
                        'source': bill_data.get('source', 'SANSAD'),
                        'house': bill_data.get('house', 'LOK_SABHA'),
                        'status': bill_data.get('status', 'PENDING'),
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
        
        logger.info("=" * 60)
        logger.info("SANSAD SCRAPING RESULTS:")
        logger.info(f"  - Created: {results['created']}")
        logger.info(f"  - Updated: {results['updated']}")
        logger.info(f"  - Failed: {results['failed']}")
        logger.info("=" * 60)
        
        return results


def run_sansad_scraper():
    scraper = SansadBillScraper()
    return scraper.scrape_all()