# tracker/middleware.py
import threading
import time
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Bill

class AutoScrapeMiddleware:
    """Middleware that checks if scraping is needed and triggers it"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_scrape = None
        self.scrape_lock = threading.Lock()
    
    def __call__(self, request):
        # Check if we need to scrape (every hour)
        self.check_and_scrape()
        
        response = self.get_response(request)
        return response
    
    def check_and_scrape(self):
        """Check if scraping is needed and trigger in background"""
        now = timezone.now()
        
        # Scrape if never scraped or last scrape was more than 6 hours ago
        should_scrape = (
            self.last_scrape is None or 
            (now - self.last_scrape) > timedelta(hours=6)
        )
        
        if should_scrape and self.scrape_lock.acquire(blocking=False):
            # Run in background thread
            thread = threading.Thread(target=self._scrape_background)
            thread.daemon = True
            thread.start()
    
    def _scrape_background(self):
        """Background scraping task"""
        try:
            print("📡 Background auto-scrape starting...")
            
            from .scraper import RealBillScraper
            scraper = RealBillScraper()
            results = scraper.scrape_all()
            
            self.last_scrape = timezone.now()
            print(f"✅ Background auto-scrape complete: {results}")
            
        except Exception as e:
            print(f"❌ Background auto-scrape error: {e}")
        finally:
            self.scrape_lock.release()