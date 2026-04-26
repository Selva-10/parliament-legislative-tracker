# scrape_state_bills_fixed.py
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
    
    # Try both URL formats
    state_slug = state_name.lower().replace(' ', '-')
    urls = [
        f"https://prsindia.org/bills/states?title=&state={state_name}&year=All",
        f"https://prsindia.org/bills/states/{state_slug}",
        f"https://prsindia.org/legislatures/states/{state_slug}/bills",
    ]
    
    bills = []
    
    for url in urls:
        print(f"   Trying: {url}")
        try:
            response = scraper.get(url, timeout=30)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different selectors
            bill_items = soup.find_all('div', class_='views-row')
            if not bill_items:
                bill_items = soup.find_all('tr')
            if not bill_items:
                bill_items = soup.find_all('a', href=True)
            
            for item in bill_items:
                # Get title from link
                link = item.find('a') if item.name != 'a' else item
                if link and link.get('href'):
                    title = link.get_text(strip=True)
                    if title and ('Bill' in title or 'Act' in title) and len(title) > 20:
                        year_match = re.search(r'202[4-6]', title)
                        year = year_match.group() if year_match else '2026'
                        bills.append({
                            'title': title,
                            'state': state_name,
                            'year': year
                        })
            
            if bills:
                print(f"   ✅ Found {len(bills)} bills for {state_name} using URL: {url}")
                break
                
        except Exception as e:
            print(f"   Error: {e}")
            continue
        
        time.sleep(1)
    
    return bills

# States to scrape
states = [
    'Karnataka',  # Already have
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
    'Delhi',
]

print("=" * 60)
print("SCRAPING STATE BILLS FROM PRS INDIA")
print("=" * 60)

all_bills = []
for state in states:
    print(f"\n📋 Processing {state}...")
    bills = scrape_state_bills(state)
    all_bills.extend(bills)
    time.sleep(2)  # Delay between states

# Remove duplicates by title
unique_bills = {}
for bill in all_bills:
    if bill['title'] not in unique_bills:
        unique_bills[bill['title']] = bill

all_bills = list(unique_bills.values())

# Save to CSV
with open('all_state_bills_fixed.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['title', 'state', 'year'])
    writer.writeheader()
    writer.writerows(all_bills)

print(f"\n{'='*60}")
print(f"✅ TOTAL UNIQUE BILLS SCRAPED: {len(all_bills)}")
print(f"✅ Saved to: all_state_bills_fixed.csv")
print(f"{'='*60}")

# Show per state
state_summary = {}
for bill in all_bills:
    state = bill['state']
    state_summary[state] = state_summary.get(state, 0) + 1

print("\n📊 BILLS PER STATE:")
for state, count in sorted(state_summary.items(), key=lambda x: x[1], reverse=True):
    print(f"   {state}: {count} bills")