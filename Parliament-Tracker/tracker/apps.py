# tracker/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def initialize_app_data(sender, **kwargs):
    """
    This function will run AFTER migrations are complete
    and the database is ready
    """
    # Import models inside the function to avoid early loading
    from .models import ScrapingSource, PoliticalParty
    
    # Now it's safe to query the database
    # Check if we need to create default data
    if not ScrapingSource.objects.exists():
        # Create default scraping sources
        ScrapingSource.objects.get_or_create(
            name="PRS Legislature",
            source_type="prs",
            url="https://prsindia.org/bill-tracker",
            is_active=True
        )
        ScrapingSource.objects.get_or_create(
            name="Lok Sabha",
            source_type="loksabha",
            url="https://loksabha.nic.in/bills",
            is_active=True
        )
    
    # Initialize default political parties if none exist
    if not PoliticalParty.objects.exists():
        parties = [
            {"name": "Bharatiya Janata Party", "short_name": "BJP", "color_code": "#FF9933"},
            {"name": "Indian National Congress", "short_name": "INC", "color_code": "#00BFFF"},
            {"name": "Aam Aadmi Party", "short_name": "AAP", "color_code": "#0000FF"},
        ]
        for party_data in parties:
            PoliticalParty.objects.get_or_create(**party_data)

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    
    def ready(self):
        """
        This method runs when the app is loaded.
        Instead of querying directly here, connect to post_migrate signal
        """
        # Connect to post_migrate signal - this ensures database is ready
        post_migrate.connect(initialize_app_data, sender=self)
# tracker/apps.py
from django.apps import AppConfig

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    
    def ready(self):
        """Initialize app data when the app is ready"""
        # Import here to avoid circular imports
        try:
            from .models import ScrapeSource  # Changed from ScrapingSource to ScrapeSource
            # Initialize any app data if needed
            pass
        except ImportError:
            pass
        except Exception as e:
            print(f"Error in app ready: {e}")

# tracker/apps.py
from django.apps import AppConfig

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    
    def ready(self):
        """Initialize app data when the app is ready"""
        # Import here to avoid circular imports
        try:
            from .models import ScrapeSource  # Note: ScrapeSource, not ScrapingSource
            # You can add initialization code here if needed
            pass
        except ImportError:
            pass
        except Exception as e:
            print(f"Error in app ready: {e}")
# tracker/apps.py
from django.apps import AppConfig
import threading
import time
import logging

logger = logging.getLogger(__name__)

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    
    def ready(self):
        """Start auto-scraping when Django starts"""
        import os
        if os.environ.get('RUN_MAIN') == 'true':  # Prevent double execution
            self.start_scraper_thread()
    
    def start_scraper_thread(self):
        """Start background thread for auto-scraping"""
        def scrape_loop():
            time.sleep(5)  # Wait for server to fully start
            logger.info("🚀 Auto-scraper thread started")
            
            # Import here to avoid circular imports
            from .management.commands.autoscrape import Command
            cmd = Command()
            
            while True:
                try:
                    logger.info("📡 Running auto-scrape...")
                    # Use the scraper directly
                    from .scraper import RealBillScraper
                    scraper = RealBillScraper()
                    results = scraper.scrape_all()
                    
                    logger.info(f"✅ Auto-scrape complete: {results}")
                    
                    # Wait 6 hours before next scrape
                    logger.info("⏰ Waiting 6 hours until next scrape...")
                    time.sleep(6 * 60 * 60)  # 6 hours
                    
                except Exception as e:
                    logger.error(f"❌ Auto-scrape error: {e}")
                    time.sleep(60)  # Wait 1 minute on error
        
        thread = threading.Thread(target=scrape_loop, daemon=True)
        thread.start()
        logger.info("🔄 Auto-scraper thread initiated")
# tracker/apps.py
from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    
    def ready(self):
        """Start auto-scraping when Django starts"""
        if os.environ.get('RUN_MAIN') == 'true':  # Prevent double execution
            from .auto_scraper import auto_scraper
            auto_scraper.start()
# tracker/apps.py
from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)

# tracker/apps.py
from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    
    def ready(self):
        """Start auto-scraping when Django starts"""
        if os.environ.get('RUN_MAIN') == 'true':  # Prevent double execution
            from .auto_scraper import auto_scraper
            auto_scraper.start()
            logger.info("Auto-scraper initialized")
def ready(self):
    if os.environ.get('RUN_MAIN') == 'true':
        from .auto_scraper import auto_scraper
        auto_scraper.start()
        