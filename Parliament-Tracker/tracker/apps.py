# tracker/apps.py
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    
    def ready(self):
        """Start auto-scraper when Django starts (in production)"""
        import os
        
        # Only start in production (not during migrations or shell)
        if os.environ.get('RUN_MAIN') or os.environ.get('DJANGO_AUTORELOAD'):
            try:
                from .auto_scraper import start_auto_scraper
                start_auto_scraper()
                logger.info("✅ Auto-scraper started from apps.py")
            except Exception as e:
                logger.error(f"Failed to start auto-scraper: {e}")