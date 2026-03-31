import time
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from tracker.models import State, Party, MP

class Command(BaseCommand):
    help = 'Scrape MPs from PRS India'

    def add_arguments(self, parser):
        parser.add_argument(
            '--save-page',
            action='store_true',
            help='Save the HTML page source for debugging',
        )

    def handle(self, *args, **options):
        self.save_page = options['save_page']
        self.stdout.write('Starting MP scraper...')
        self.setup_driver()
        self.scrape_mps()
        self.driver.quit()
        self.stdout.write(self.style.SUCCESS('MP scraping completed.'))

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

    def scrape_mps(self):
        url = "https://prsindia.org/mptrack"
        self.driver.get(url)
        if self.save_page:
            self.save_page_source('mp_track_initial.html')
        self.wait_for_all_content()
        if self.save_page:
            self.save_page_source('mp_track_final.html')
        self.parse_page()

    def wait_for_all_content(self):
        """Scroll and click 'Load More' if present."""
        time.sleep(3)
        last_count = 0
        no_change_count = 0
        max_attempts = 100
        target_count = 543
        for attempt in range(max_attempts):
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # Check for a "Load More" button and click it
            try:
                load_more = self.driver.find_element(By.CSS_SELECTOR, 'a.load-more, button.load-more, .pager-next a, .view-more a')
                if load_more.is_displayed():
                    self.driver.execute_script("arguments[0].click();", load_more)
                    self.stdout.write("Clicked 'Load More'.")
                    time.sleep(3)
            except:
                pass

            # Count current rows
            current_rows = self.driver.find_elements(By.CSS_SELECTOR, '.views-row')
            current_count = len(current_rows)
            self.stdout.write(f"Attempt {attempt+1}: Found {current_count} MPs.")

            if current_count >= target_count:
                break

            if current_count == last_count:
                no_change_count += 1
            else:
                no_change_count = 0
            last_count = current_count

            if no_change_count >= 5:
                self.stdout.write("No change after 5 attempts, stopping.")
                break

        self.stdout.write(f"Final MP count: {last_count}")

    def save_page_source(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        self.stdout.write(f'Saved page source to {filename}')

    def parse_page(self):
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        rows = soup.select('div.views-row')
        self.stdout.write(f'Total rows found: {len(rows)}')

        saved = 0
        for row in rows:
            party_elem = row.select_one('.views-field-field-political-party .field-content')
            party_name = party_elem.get_text(strip=True) if party_elem else ''

            name_elem = row.select_one('.views-field-title-field h3 a')
            name = name_elem.get_text(strip=True) if name_elem else ''

            state_elem = row.select_one('.views-field-field-net-revenue-railway .field-content')
            state_name = state_elem.get_text(strip=True) if state_elem else ''

            const_elem = row.select_one('.views-field-php .field-content')
            constituency = const_elem.get_text(strip=True) if const_elem else ''

            if not name:
                continue

            state, _ = State.objects.get_or_create(name=state_name) if state_name else (None, None)
            party, _ = Party.objects.get_or_create(name=party_name) if party_name else (None, None)

            house = 'LOK_SABHA'

            MP.objects.update_or_create(
                name=name,
                state=state,
                constituency=constituency,
                defaults={'house': house, 'party': party}
            )
            saved += 1

        self.stdout.write(self.style.SUCCESS(f'Saved {saved} MPs.'))
           