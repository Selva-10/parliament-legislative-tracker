# tracker/auto_scraper.py
import threading
import time
import logging
from django.utils import timezone
from .models import Bill

logger = logging.getLogger(__name__)

class AutoScraper:
    _instance = None
    _thread = None
    _running = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Auto-scraper started (running every hour)")

    def stop(self):
        self._running = False
        logger.info("Auto-scraper stopped")

    def _run(self):
        time.sleep(5)
        from .scraper import RealBillScraper
        scraper = RealBillScraper()

        while self._running:
            try:
                logger.info("Auto-scraping new bills...")
                bills = scraper.scrape_today_bills()
                if bills:
                    # Use get_or_create to avoid duplicates
                    for bill_data in bills:
                        Bill.objects.get_or_create(
                            bill_id=bill_data['bill_id'],
                            defaults=bill_data
                        )
                    logger.info(f"Auto-scrape complete: {len(bills)} new bills")
                else:
                    logger.info("No new bills scraped")
            except Exception as e:
                logger.error(f"Auto-scrape error: {e}")
            finally:
                # Wait 1 hour (3600 seconds) before next run
                for _ in range(60):
                    if not self._running:
                        break
                    time.sleep(60)  # check every minute, but total 60 minutes

auto_scraper = AutoScraper()