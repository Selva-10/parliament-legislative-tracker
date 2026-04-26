# scrape_karnataka_bills.py
import cloudscraper
from bs4 import BeautifulSoup
import csv
import re

# URL for Karnataka bills
url = "https://prsindia.org/bills/states?title=&state=Karnataka&year=All"

# Setup scraper
scraper = cloudscraper.create_scraper(browser={
    'browser': 'chrome',
    'platform': 'windows',
    'mobile': False
})

print(f"📋 Fetching bills for Karnataka...")
response = scraper.get(url)

if response.status_code != 200:
    print(f"❌ Failed to fetch page: {response.status_code}")
    exit()

soup = BeautifulSoup(response.text, 'html.parser')
bills = []

# Find all bill entries
# Each bill is in a container like div.views-row
bill_items = soup.find_all('div', class_='views-row')

if not bill_items:
    # Alternative: find all links containing 'Bill'
    bill_items = soup.find_all('a', href=True)
    
    for item in bill_items:
        title = item.get_text(strip=True)
        if title and 'Bill, 202' in title:
            bills.append({
                'title': title,
                'state': 'Karnataka',
                'year': re.search(r'202[4-6]', title).group() if re.search(r'202[4-6]', title) else '2026'
            })
else:
    # Parse each bill item
    for item in bill_items:
        # Get title from link
        link = item.find('a')
        if not link:
            continue
        
        title = link.get_text(strip=True)
        if not title or 'Bill' not in title:
            continue
        
        # Get state (from class or text)
        state_elem = item.find('div', class_='views-field-field-state')
        state = state_elem.get_text(strip=True) if state_elem else 'Karnataka'
        
        # Extract year
        year_match = re.search(r'202[4-6]', title)
        year = year_match.group() if year_match else '2026'
        
        bills.append({
            'title': title,
            'state': state,
            'year': year
        })

print(f"✅ Found {len(bills)} bills")

# Show first 10 bills
print("\n📋 First 10 bills:")
for bill in bills[:10]:
    print(f"   {bill['title'][:70]} ({bill['state']})")

# Save to CSV
with open('karnataka_bills.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['title', 'state', 'year'])
    writer.writeheader()
    writer.writerows(bills)

print(f"\n✅ Saved {len(bills)} bills to karnataka_bills.csv")