# tracker/prs_scraper.py
import cloudscraper
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from django.utils import timezone
from .models import Bill
import re
import time
import json
import requests

logger = logging.getLogger(__name__)

class PRSScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False,
                'custom': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        logger.info("PRS Scraper initialized")

    def _parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str or date_str.strip() == '':
            return None
        
        date_str = str(date_str).strip()
        
        # Remove common prefixes
        date_str = re.sub(r'(Introduced on|Date:|Introduction Date:|Passed on|Posted on)', '', date_str, flags=re.IGNORECASE)
        date_str = date_str.strip()
        
        # Try different formats
        formats = [
            '%d %B %Y',      # 16 April 2026
            '%B %d, %Y',     # April 16, 2026
            '%d-%m-%Y',      # 16-04-2026
            '%d/%m/%Y',      # 16/04/2026
            '%Y-%m-%d',      # 2026-04-16
            '%d %b %Y',      # 16 Apr 2026
            '%b %d, %Y',     # Apr 16, 2026
            '%d.%m.%Y',      # 16.04.2026
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                if 2000 <= parsed.year <= 2030:
                    return parsed
            except ValueError:
                continue
        
        # Try regex for DD/MM/YYYY
        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
        if date_match:
            try:
                day, month, year = date_match.groups()
                return datetime(int(year), int(month), int(day)).date()
            except ValueError:
                pass
        
        return None

    def scrape_from_rss(self):
        """Scrape PRS using their RSS feed (most reliable)"""
        logger.info("=" * 60)
        logger.info("Scraping PRS via RSS Feed")
        logger.info("=" * 60)
        
        bills = []
        rss_urls = [
            "https://www.prsindia.org/rss/bills.xml",
            "https://www.prsindia.org/rss/parliament.xml",
            "https://www.prsindia.org/rss/billtrack.xml",
        ]
        
        for url in rss_urls:
            try:
                response = self.scraper.get(url, timeout=30)
                if response.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)
                    
                    for item in root.findall('.//item'):
                        title = item.find('title').text if item.find('title') is not None else ''
                        link = item.find('link').text if item.find('link') is not None else ''
                        pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                        description = item.find('description').text if item.find('description') is not None else ''
                        
                        if title and 'bill' in title.lower():
                            intro_date = self._parse_date(pub_date)
                            
                            bill_id = f"PRS-RSS-{abs(hash(title)) % 10000:04d}"
                            bills.append({
                                'bill_id': bill_id,
                                'title': title,
                                'introduction_date': intro_date,
                                'prs_link': link,
                                'description': description[:500] if description else '',
                                'source': 'PRS_RSS',
                                'status': 'PENDING',
                            })
                            logger.info(f"  RSS: {title[:50]}")
                            
            except Exception as e:
                logger.error(f"RSS error for {url}: {e}")
        
        logger.info(f"Found {len(bills)} bills from RSS")
        return bills

    def scrape_from_github_dataset(self):
        """Import from pre-scraped GitHub dataset"""
        logger.info("=" * 60)
        logger.info("Importing PRS Data from GitHub")
        logger.info("=" * 60)
        
        bills = []
        
        # GitHub dataset URLs
        urls = [
            "https://raw.githubusercontent.com/Vonter/india-representatives-activity/main/data/18_ls/private_member_bills_18_ls.json",
            "https://raw.githubusercontent.com/Vonter/india-representatives-activity/main/data/17_ls/private_member_bills_17_ls.json",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Loaded {len(data)} records from {url.split('/')[-1]}")
                    
                    for item in data:
                        title = item.get('title', item.get('bill_title', ''))
                        date_str = item.get('date_introduced', '')
                        intro_date = self._parse_date(date_str)
                        member_name = item.get('member_name', '')
                        
                        if title:
                            bill_id = f"PRS-GH-{abs(hash(title)) % 10000:04d}"
                            bills.append({
                                'bill_id': bill_id,
                                'title': title,
                                'introduction_date': intro_date,
                                'introduced_by': member_name,
                                'source': 'PRS_GITHUB',
                                'status': 'PENDING',
                            })
                            logger.info(f"  GitHub: {title[:50]}")
                            
            except Exception as e:
                logger.error(f"GitHub error for {url}: {e}")
        
        logger.info(f"Found {len(bills)} bills from GitHub dataset")
        return bills

    def scrape_bill_detail_page(self, bill_url):
        """Scrape individual bill detail page for passed dates"""
        try:
            response = self.scraper.get(bill_url, timeout=30)
            if response.status_code != 200:
                return None, None
            
            page_text = response.text
            
            # Look for Lok Sabha passed date
            ls_patterns = [
                r'Passed in Lok Sabha on\s*:?\s*(\d{1,2}\s+\w+\s+\d{4})',
                r'Lok Sabha\s*:?\s*Passed on\s*(\d{1,2}/\d{1,2}/\d{4})',
                r'LS Passed\s*:?\s*(\d{1,2}-\d{1,2}-\d{4})',
                r'Lok Sabha.*?(\d{1,2}\s+\w+\s+\d{4})',
            ]
            
            # Look for Rajya Sabha passed date
            rs_patterns = [
                r'Passed in Rajya Sabha on\s*:?\s*(\d{1,2}\s+\w+\s+\d{4})',
                r'Rajya Sabha\s*:?\s*Passed on\s*(\d{1,2}/\d{1,2}/\d{4})',
                r'RS Passed\s*:?\s*(\d{1,2}-\d{1,2}-\d{4})',
                r'Rajya Sabha.*?(\d{1,2}\s+\w+\s+\d{4})',
            ]
            
            passed_ls = None
            passed_rs = None
            
            for pattern in ls_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    passed_ls = self._parse_date(match.group(1))
                    break
            
            for pattern in rs_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    passed_rs = self._parse_date(match.group(1))
                    break
            
            return passed_ls, passed_rs
            
        except Exception as e:
            logger.error(f"Error scraping detail page {bill_url}: {e}")
            return None, None

    def scrape_bill_list_page(self):
        """Scrape bill list page from PRS India"""
        logger.info("=" * 60)
        logger.info("Scraping PRS Bill List Page")
        logger.info("=" * 60)
        
        bills = []
        urls = [
            "https://www.prsindia.org/billtrack",
            "https://www.prsindia.org/billtrack/government-bills",
            "https://www.prsindia.org/billtrack/private-member-bills",
        ]
        
        for url in urls:
            try:
                response = self.scraper.get(url, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try multiple selectors for bill items
                selectors = [
                    '.view-billtrack',
                    '.view-content',
                    'article',
                    '.views-row',
                    '.bill-item',
                ]
                
                for selector in selectors:
                    items = soup.select(selector)
                    if items:
                        logger.info(f"Found {len(items)} items with selector: {selector}")
                        
                        for item in items:
                            # Find title and link
                            link = item.find('a', href=True)
                            if link and ('/bill/' in link['href'] or '/bill-details/' in link['href']):
                                title = link.get_text(strip=True)
                                href = link['href']
                                full_url = href if href.startswith('http') else 'https://www.prsindia.org' + href
                                
                                if title and len(title) > 10:
                                    bill_id = f"PRS-LIST-{abs(hash(title)) % 10000:04d}"
                                    bills.append({
                                        'bill_id': bill_id,
                                        'title': title,
                                        'prs_link': full_url,
                                        'source': 'PRS_LIST',
                                        'status': 'PENDING',
                                    })
                                    logger.info(f"  List: {title[:50]}")
                        
                        # Break if we found items
                        if bills:
                            break
                
                time.sleep(2)  # Be respectful
                
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
        
        # Remove duplicates by title
        unique_bills = {}
        for bill in bills:
            title_key = bill['title'].lower()
            if title_key not in unique_bills:
                unique_bills[title_key] = bill
        
        logger.info(f"Found {len(unique_bills)} unique bills from list pages")
        return list(unique_bills.values())

    def scrape_all(self):
        """Main scraping method - combines all PRS sources"""
        all_bills = []
        
        logger.info("=" * 60)
        logger.info("PRS INDIA COMPREHENSIVE SCRAPER")
        logger.info("=" * 60)
        
        # Method 1: RSS Feed (Most reliable)
        rss_bills = self.scrape_from_rss()
        all_bills.extend(rss_bills)
        
        # Method 2: GitHub Dataset (Pre-scraped)
        github_bills = self.scrape_from_github_dataset()
        all_bills.extend(github_bills)
        
        # Method 3: List Page (If accessible)
        list_bills = self.scrape_bill_list_page()
        all_bills.extend(list_bills)
        
        # Remove duplicates by title
        unique_bills = {}
        for bill in all_bills:
            title_key = bill['title'].lower()
            if title_key not in unique_bills:
                unique_bills[title_key] = bill
        
        all_bills = list(unique_bills.values())
        
        logger.info(f"\n📊 TOTAL BILLS COLLECTED: {len(all_bills)}")
        
        if not all_bills:
            logger.warning("No bills fetched from any PRS source")
            return {'created': 0, 'updated': 0, 'failed': 0}
        
        # Save to database
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
                        'introduced_by': bill_data.get('introduced_by', ''),
                        'description': bill_data.get('description', ''),
                        'source': bill_data.get('source', 'PRS_INDIA'),
                        'prs_link': bill_data.get('prs_link', ''),
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
        logger.info("PRS SCRAPING RESULTS:")
        logger.info(f"  - Created: {results['created']}")
        logger.info(f"  - Updated: {results['updated']}")
        logger.info(f"  - Failed: {results['failed']}")
        logger.info("=" * 60)
        
        return results


# Helper function to run from command line
def run_prs_scraper():
    scraper = PRSScraper()
    return scraper.scrape_all()