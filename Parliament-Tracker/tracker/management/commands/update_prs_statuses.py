# tracker/management/commands/update_prs_statuses.py
from django.core.management.base import BaseCommand
from tracker.prs_status_updater import update_statuses_from_prs
from datetime import datetime
import time

class Command(BaseCommand):
    help = 'Scrape bill statuses from PRS India (by year) and update MPA bills'

    def handle(self, *args, **options):
        self.stdout.write(f"\n🚀 Starting PRS status update at {datetime.now()}")
        self.stdout.write("=" * 50)

        start_time = time.time()

        try:
            result = update_statuses_from_prs()
            elapsed = time.time() - start_time

            self.stdout.write(self.style.SUCCESS(
                f"\n✅ Complete! Updated {result['updated']} out of {result['matched']} matched MPA bills."
            ))
            self.stdout.write(f"📊 Scraped {result['scraped']} statuses from PRS (2019-2026).")
            self.stdout.write(f"⏱️ Time taken: {elapsed:.1f} seconds.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Failed: {e}"))
            import traceback
            traceback.print_exc()