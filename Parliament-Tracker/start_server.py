# start_server.py
import subprocess
import sys
import threading
import time

def run_scraper():
    """Run scraper in background"""
    time.sleep(3)  # Wait for server to start
    print("🚀 Starting background auto-scraper...")
    
    from tracker.auto_scraper import auto_scraper
    auto_scraper.start()

def run_server():
    """Run Django server"""
    print("🌐 Starting Django server...")
    subprocess.run([sys.executable, "manage.py", "runserver"])

if __name__ == "__main__":
    # Start scraper in background thread
    scraper_thread = threading.Thread(target=run_scraper, daemon=True)
    scraper_thread.start()
    
    # Run server in main thread