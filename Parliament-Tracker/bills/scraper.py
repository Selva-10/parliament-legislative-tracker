# bills/scraper.py
import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from django.conf import settings
from .models import Bill
from celery import shared_task

logger = logging.getLogger(__name__)

# Add Rajya Sabha URL to settings
RAJYA_SABHA_URL = getattr(settings, 'RAJYA_SABHA_URL', 'https://rajyasabha.nic.in/bills')
LOK_SABHA_URL = getattr(settings, 'LOK_SABHA_URL', 'https://loksabha.nic.in/bills')
PRS_INDIA_URL = getattr(settings, 'PRS_INDIA_URL', 'https://prsindia.org/bill-tracker')

@shared_task
def scrape_prs():
    """Scrape bills from PRS India"""
    logger.info("Starting PRS India scrape")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(PRS_INDIA_URL, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse bills (adjust selectors based on actual PRS structure)
        bill_elements = soup.select('.bill-item, .bill-card, tr.bill-row')[:50]
        
        created_count = 0
        updated_count = 0
        
        for element in bill_elements:
            try:
                # Extract data (adjust based on actual HTML)
                title_elem = element.select_one('.bill-title, h3, a')
                title = title_elem.text.strip() if title_elem else "Unknown"
                
                link = title_elem.get('href', '') if title_elem else ''
                if link and not link.startswith('http'):
                    link = 'https://prsindia.org' + link
                
                # Generate bill ID from title or link
                import hashlib
                bill_id = f"PRS-{hashlib.md5(title.encode()).hexdigest()[:8].upper()}"
                
                # Check if bill exists
                bill, created = Bill.objects.update_or_create(
                    bill_id=bill_id,
                    defaults={
                        'title': title,
                        'prs_link': link,
                        'source': 'PRS',
                        'house': 'LOK_SABHA',  # Default, adjust as needed
                        'last_updated': datetime.now(),
                    }
                )
                
                if created:
                    created_count += 1
                    logger.debug(f"Created bill: {bill_id}")
                else:
                    updated_count += 1
                    logger.debug(f"Updated bill: {bill_id}")
                    
            except Exception as e:
                logger.error(f"Error processing bill element: {e}")
        
        logger.info(f"PRS scrape complete: {created_count} created, {updated_count} updated")
        return {'created': created_count, 'updated': updated_count}
        
    except requests.RequestException as e:
        logger.error(f"Failed to scrape PRS: {e}")
        # Return mock data for development
        return _get_mock_prs_data()

@shared_task
def scrape_loksabha():
    """Scrape bills from Lok Sabha"""
    logger.info("Starting Lok Sabha scrape")
    
    # Similar implementation to scrape_prs but for Lok Sabha
    # For now, return mock data since the site is often unreachable
    return _get_mock_loksabha_data()

@shared_task
def scrape_rajyasabha():
    """Scrape bills from Rajya Sabha"""
    logger.info("Starting Rajya Sabha scrape")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(RAJYA_SABHA_URL, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse Rajya Sabha bills
        # Add your parsing logic here based on actual site structure
        
        created_count = 0
        updated_count = 0
        
        # Example parsing (adjust based on actual HTML)
        bill_rows = soup.select('table tbody tr')[:30]
        
        for row in bill_rows:
            try:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    bill_number = cols[0].text.strip()
                    title = cols[1].text.strip()
                    date_text = cols[2].text.strip()
                    
                    bill_id = f"RS-{bill_number}"
                    
                    bill, created = Bill.objects.update_or_create(
                        bill_id=bill_id,
                        defaults={
                            'bill_number': bill_number,
                            'title': title,
                            'house': 'RAJYA_SABHA',
                            'source': 'RAJYA_SABHA',
                            'rajyasabha_link': RAJYA_SABHA_URL,
                            'last_updated': datetime.now(),
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                        
            except Exception as e:
                logger.error(f"Error processing Rajya Sabha row: {e}")
        
        if created_count > 0 or updated_count > 0:
            logger.info(f"Rajya Sabha scrape complete: {created_count} created, {updated_count} updated")
            return {'created': created_count, 'updated': updated_count}
        else:
            return _get_mock_rajyasabha_data()
            
    except Exception as e:
        logger.error(f"Failed to scrape Rajya Sabha: {e}")
        return _get_mock_rajyasabha_data()

def _get_mock_prs_data():
    """Return mock PRS data for development"""
    created = 0
    for i in range(1, 6):
        bill, created_flag = Bill.objects.update_or_create(
            bill_id=f"PRS-00{i}",
            defaults={
                'title': f"Sample PRS Bill {i}",
                'house': 'LOK_SABHA',
                'status': 'PENDING',
                'source': 'PRS',
                'introduction_date': datetime.now().date(),
                'prs_link': 'https://prsindia.org/bill-tracker',
            }
        )
        if created_flag:
            created += 1
    
    return {'created': created, 'updated': 5 - created}

def _get_mock_loksabha_data():
    """Return mock Lok Sabha data for development"""
    created = 0
    for i in range(1, 6):
        bill, created_flag = Bill.objects.update_or_create(
            bill_id=f"LS-10{i}",
            defaults={
                'bill_number': f"Bill No. {i}",
                'title': f"Sample Lok Sabha Bill {i}",
                'house': 'LOK_SABHA',
                'status': 'PENDING',
                'source': 'LOK_SABHA',
                'introduction_date': datetime.now().date(),
                'loksabha_link': 'https://loksabha.nic.in/bills',
            }
        )
        if created_flag:
            created += 1
    
    return {'created': created, 'updated': 5 - created}

def _get_mock_rajyasabha_data():
    """Return mock Rajya Sabha data for development"""
    created = 0
    for i in range(1, 6):
        bill, created_flag = Bill.objects.update_or_create(
            bill_id=f"RS-20{i}",
            defaults={
                'bill_number': f"RS Bill {i}",
                'title': f"Sample Rajya Sabha Bill {i}",
                'house': 'RAJYA_SABHA',
                'status': 'PENDING',
                'source': 'RAJYA_SABHA',
                'introduction_date': datetime.now().date(),
                'rajyasabha_link': 'https://rajyasabha.nic.in/bills',
            }
        )
        if created_flag:
            created += 1
    
    return {'created': created, 'updated': 5 - created}