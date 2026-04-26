# check_mla.py
import os
from bs4 import BeautifulSoup

html_file = 'mla_Karnataka.html'

if not os.path.exists(html_file):
    print(f"File not found: {html_file}")
    # List all MLA files
    for f in os.listdir('.'):
        if f.startswith('mla_') and f.endswith('.html'):
            print(f"Found: {f}")
    exit()

print(f"\n=== Analyzing {html_file} ===\n")

with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()
    soup = BeautifulSoup(content, 'html.parser')

# Print first 2000 characters
print("FIRST 2000 CHARACTERS:")
print("-" * 40)
print(content[:2000])
print("-" * 40)

# Check for tables
tables = soup.find_all('table')
print(f"\nNumber of tables: {len(tables)}")

if tables:
    for i, table in enumerate(tables):
        rows = table.find_all('tr')
        print(f"Table {i}: {len(rows)} rows")
        if rows:
            first_row = rows[0]
            cells = first_row.find_all(['th', 'td'])
            print(f"  Headers: {[c.get_text(strip=True)[:30] for c in cells]}")
else:
    print("No tables found")

# Check for divs with class 'views-row'
view_rows = soup.find_all('div', class_='views-row')
print(f"\nDivs with class 'views-row': {len(view_rows)}")

# Check for any text that looks like MLA names
text = soup.get_text()
lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 10]
print(f"\nFirst 10 non-empty lines of text:")
for line in lines[:10]:
    print(f"  {line[:80]}")