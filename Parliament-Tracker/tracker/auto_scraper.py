# tracker/auto_scraper.py
import threading
import time
import logging
from datetime import datetime

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
        logger.info("Auto-scraper started (running daily)")

    def stop(self):
        self._running = False
        logger.info("Auto-scraper stopped")

    def _run(self):
        time.sleep(30)
        from .scraper import RealBillScraper
        scraper = RealBillScraper()

        while self._running:
            try:
                logger.info(f"Auto-scraping Parliament bills at {datetime.now()}")
                result = scraper.scrape_all()
                logger.info(f"Auto-scrape complete: {result}")
            except Exception as e:
                logger.error(f"Auto-scrape error: {e}")

            # Wait 24 hours before next scrape
            for _ in range(86400):
                if not self._running:
                    break
                time.sleep(1)

auto_scraper = AutoScraper()