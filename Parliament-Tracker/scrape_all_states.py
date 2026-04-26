# scrape_all_states.py
import cloudscraper
from bs4 import BeautifulSoup
import csv
import re
import time

def scrape_state_bills(state_name):
    """Scrape bills for any state from PRS India"""
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    })
    
    # Create URL with state name
    url = f"https://prsindia.org/bills/states?title=&state={state_name}&year=All"
    
    print(f"📋 Fetching bills for {state_name}...")
    
    try:
        response = scraper.get(url, timeout=30)
        if response.status_code != 200:
            print(f"   ❌ Failed (Status: {response.status_code})")
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
                    # Extract year from title
                    year_match = re.search(r'202[4-6]', title)
                    year = year_match.group() if year_match else '2026'
                    
                    bills.append({
                        'title': title,
                        'state': state_name,
                        'year': year
                    })
        
        print(f"   ✅ Found {len(bills)} bills for {state_name}")
        return bills
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

# States to scrape
states = [
    'Maharashtra',
    'Tamil Nadu', 
    'Gujarat',
    'Kerala',
    'Punjab',
    'West Bengal',
    'Rajasthan',
    'Uttar Pradesh',
    'Madhya Pradesh',
    'Bihar',
    'Odisha',
    'Telangana',
    'Andhra Pradesh',
    'Haryana',
    'Delhi'
]

print("=" * 60)
print("SCRAPING STATE BILLS FROM PRS INDIA")
print("=" * 60)

all_bills = []
for state in states:
    bills = scrape_state_bills(state)
    all_bills.extend(bills)
    time.sleep(2)  # Wait 2 seconds between states

# Save all bills to CSV
with open('all_state_bills.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['title', 'state', 'year'])
    writer.writeheader()
    writer.writerows(all_bills)

print(f"\n{'='*60}")
print(f"✅ TOTAL BILLS SCRAPED: {len(all_bills)}")
print(f"✅ Saved to: all_state_bills.csv")
print(f"{'='*60}")