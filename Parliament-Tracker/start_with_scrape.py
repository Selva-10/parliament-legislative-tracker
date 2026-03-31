# start_with_scrape.py
import subprocess
import sys
import time

print("📡 Fetching latest bills...")
result = subprocess.run([sys.executable, "manage.py", "scrape_today"], capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Scraping completed successfully")
    if result.stdout:
        print(result.stdout)
else:
    print("❌ Scraping failed")
    print(result.stderr)

print("\n🚀 Starting server...")
subprocess.run([sys.executable, "manage.py", "runserver"])