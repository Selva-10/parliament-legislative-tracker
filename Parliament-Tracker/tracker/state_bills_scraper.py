# tracker/state_bills_scraper.py
import cloudscraper
from bs4 import BeautifulSoup
import csv
import time

class StateBillsScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        })
    
    def scrape_state_bills(self, state_name):
        """Scrape bills for a specific state from PRS"""
        state_slug = state_name.lower().replace(' ', '-')
        url = f"https://prsindia.org/bills/states?title=&state={state_name}&year=All"
        
        print(f"📋 Fetching bills for {state_name}...")
        
        try:
            response = self.scraper.get(url, timeout=30)
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
                        bills.append({
                            'title': title,
                            'state': state_name,
                            'year': '2026'
                        })
            
            print(f"   ✅ Found {len(bills)} bills for {state_name}")
            return bills
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []
    
    def scrape_all_states(self):
        """Scrape bills for all major Indian states"""
        states = [
            'Karnataka', 'Maharashtra', 'Tamil Nadu', 'Gujarat', 
            'Kerala', 'Punjab', 'West Bengal', 'Delhi', 'Uttar Pradesh',
            'Rajasthan', 'Madhya Pradesh', 'Bihar', 'Odisha', 'Telangana'
        ]
        
        all_bills = []
        for state in states:
            bills = self.scrape_state_bills(state)
            all_bills.extend(bills)
            time.sleep(2)  # Respectful delay
        
        return all_bills

# Run scraper
if __name__ == "__main__":
    scraper = StateBillsScraper()
    bills = scraper.scrape_all_states()
    
    # Save to CSV
    with open('all_state_bills.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'state', 'year'])
        writer.writeheader()
        writer.writerows(bills)
    
    print(f"\n✅ Total bills scraped: {len(bills)}")