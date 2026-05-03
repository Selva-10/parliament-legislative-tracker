# tracker/auto_scraper.py
import logging
import time
import schedule
import threading
from datetime import datetime
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

class AutoBillScraper:
    """Automatic bill scraper with integrated house and status updates from PRS"""
    
    def __init__(self):
        self.scraping_in_progress = False
        self.last_run = None
        self.scheduler_thread = None
        self.running = False
        
    def scrape_mpa_bills(self):
        """Scrape bills from MPA website"""
        from .scraper import RealBillScraper
        
        logger.info("Auto-scraping MPA bills...")
        try:
            scraper = RealBillScraper()
            result = scraper.scrape_mpa_bills()
            
            if result:
                saved = self._save_bills_to_db(result, 'MPA')
                logger.info(f"MPA auto-scrape complete: {saved} bills saved")
                return saved
            return 0
        except Exception as e:
            logger.error(f"MPA auto-scrape failed: {e}")
            return 0
    
    def scrape_state_bills(self):
        """Scrape bills from Indian states"""
        try:
            from .state_scraper import scrape_all_state_bills
            logger.info("Auto-scraping State bills...")
            saved = scrape_all_state_bills()
            logger.info(f"State bills auto-scrape complete: {saved} bills saved")
            return saved
        except Exception as e:
            logger.error(f"State bills auto-scrape failed: {e}")
            return 0
    
    def scrape_prs_bills(self):
        """Scrape bills from PRS India"""
        try:
            from .prs_scraper import PRSScraper
            logger.info("Auto-scraping PRS India bills...")
            scraper = PRSScraper()
            result = scraper.scrape_all()
            
            if result:
                created = result.get('created', 0)
                updated = result.get('updated', 0)
                logger.info(f"PRS auto-scrape complete: {created} new, {updated} updated")
                return created + updated
            return 0
        except Exception as e:
            logger.error(f"PRS auto-scrape failed: {e}")
            return 0
    
    def update_house_from_prs_sessions(self):
        """Update house information from PRS session links (ALL 21 sessions)"""
        from .house_updater_complete import update_all_houses
        
        logger.info("=" * 50)
        logger.info("Updating House Information from PRS Sessions")
        logger.info("=" * 50)
        
        try:
            result = update_all_houses()
            updated = result.get('bills_updated', 0)
            scraped = result.get('bills_scraped', 0)
            logger.info(f"House update complete: {updated} bills updated from {scraped} scraped")
            return updated
        except Exception as e:
            logger.error(f"House update failed: {e}")
            return 0
    
    def update_status_from_prs(self):
        """Update bill statuses from PRS billtrack page (year-wise 2019-2026)"""
        from .prs_status_updater import update_statuses_from_prs
        
        logger.info("=" * 50)
        logger.info("Updating Status Information from PRS Billtrack")
        logger.info("(Years: 2019-2026)")
        logger.info("=" * 50)
        
        try:
            result = update_statuses_from_prs()
            updated = result.get('updated', 0)
            scraped = result.get('scraped', 0)
            matched = result.get('matched', 0)
            logger.info(f"Status update complete: {updated} bills updated (matched: {matched}, scraped: {scraped})")
            return updated
        except Exception as e:
            logger.error(f"Status update failed: {e}")
            return 0
    
    def _save_bills_to_db(self, bills, source):
        """Save scraped bills to database WITHOUT creating duplicates"""
        from .models import Bill
        import hashlib
    
        saved_count = 0
        updated_count = 0
    
        for bill_data in bills:
            try:
            # Create consistent ID from title
                title = bill_data.get('title', '')
                consistent_id = f"{source}-{hashlib.md5(title.encode()).hexdigest()[:8].upper()}"
            
            # Update or create with consistent ID
                obj, created = Bill.objects.update_or_create(
                    bill_id=consistent_id,
                    defaults={
                        'title': title,
                        'bill_number': bill_data.get('bill_number', ''),
                        'introduction_date': bill_data.get('introduction_date'),
                        'passed_in_ls_date': bill_data.get('passed_in_ls_date'),
                        'passed_in_rs_date': bill_data.get('passed_in_rs_date'),
                        'ministry': bill_data.get('ministry', ''),
                        'source': source,
                        'house': bill_data.get('house', 'LOK_SABHA'),
                        'status': bill_data.get('status', 'PENDING'),
                        'last_updated': timezone.now(),
                    }
                )
            
                if created:
                    saved_count += 1
                else:
                    updated_count += 1
                
            except Exception as e:
                logger.error(f"Save error: {e}")
    
        logger.info(f"Saved: {saved_count} new, Updated: {updated_count} existing")
        return saved_count + updated_count
    
    def scrape_all_sources(self):
        """Scrape all sources and update house and status information"""
        if self.scraping_in_progress:
            logger.info("Scraping already in progress, skipping...")
            return {'mpa': 0, 'state': 0, 'prs': 0, 'house_updates': 0, 'status_updates': 0, 'skipped': True}
        
        self.scraping_in_progress = True
        self.last_run = timezone.now()
        
        logger.info("=" * 60)
        logger.info("Starting AUTO SCRAPING of all sources")
        logger.info(f"Time: {self.last_run}")
        logger.info("=" * 60)
        
        results = {}
        
        # STEP 1: Scrape MPA bills
        logger.info("\nSTEP 1: Scraping MPA Bills")
        results['mpa'] = self.scrape_mpa_bills()
        
        # STEP 2: Scrape State bills
        logger.info("\nSTEP 2: Scraping State Bills")
        results['state'] = self.scrape_state_bills()
        
        # STEP 3: Scrape PRS bills
        logger.info("\nSTEP 3: Scraping PRS Bills")
        results['prs'] = self.scrape_prs_bills()
        
        # STEP 4: Update House Information from PRS Sessions
        logger.info("\nSTEP 4: Updating House Information from PRS Sessions")
        results['house_updates'] = self.update_house_from_prs_sessions()
        
        # STEP 5: Update Status Information from PRS Billtrack (Overrides scraper.py status)
        logger.info("\nSTEP 5: Updating Status Information from PRS Billtrack")
        results['status_updates'] = self.update_status_from_prs()
        
        self.scraping_in_progress = False
        
        logger.info("\n" + "=" * 60)
        logger.info("AUTO SCRAPING COMPLETE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  MPA Bills Scraped: {results['mpa']}")
        logger.info(f"  State Bills Scraped: {results['state']}")
        logger.info(f"  PRS Bills Scraped: {results['prs']}")
        logger.info(f"  House Information Updated: {results['house_updates']} bills")
        logger.info(f"  Status Information Updated: {results['status_updates']} bills")
        logger.info("=" * 60)
        
        # Store results in cache for monitoring
        cache.set('last_auto_scrape', {
            'time': self.last_run.isoformat(),
            'results': results
        }, 3600 * 24)
        
        return results
    
    def run_scheduler(self):
        """Run the scheduler in a separate thread"""
        self.running = True
        
        # Schedule every 6 hours
        schedule.every(6).hours.do(self.scrape_all_sources)
        schedule.every().day.at("06:00").do(self.scrape_all_sources)
        schedule.every().day.at("12:00").do(self.scrape_all_sources)
        schedule.every().day.at("18:00").do(self.scrape_all_sources)
        
        logger.info("Auto-scraping scheduler started")
        logger.info("   - Every 6 hours")
        logger.info("   - Daily: 6 AM, 12 PM, 6 PM")
        
        # Run first scrape immediately
        self.scrape_all_sources()
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)
    
    def start_scheduler(self):
        """Start the scheduler in background thread"""
        if self.scheduler_thread is None or not self.scheduler_thread.is_alive():
            self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logger.info("Auto-scraping scheduler started in background")
            return True
        return False
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Auto-scraping scheduler stopped")
    
    def get_status(self):
        """Get current status of the scraper"""
        return {
            'running': self.running,
            'scraping_in_progress': self.scraping_in_progress,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False,
        }


# Singleton instance
auto_scraper = AutoBillScraper()

def start_auto_scraper():
    """Start the auto scraper (call this in apps.py)"""
    return auto_scraper.start_scheduler()

def get_scraper_status():
    """Get current scraper status for monitoring"""
    return auto_scraper.get_status()

def manual_scrape_all():
    """Manual trigger for scraping all sources"""
    return auto_scraper.scrape_all_sources()