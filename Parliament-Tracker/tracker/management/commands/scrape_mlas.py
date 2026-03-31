# tracker/management/commands/scrape_mlas.py
import time
import urllib.parse
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from tracker.models import State, Party, MLA

class Command(BaseCommand):
    help = 'Scrape MLAs from PRS India'

    def add_arguments(self, parser):
        parser.add_argument(
            '--save-page',
            action='store_true',
            help='Save HTML for debugging',
        )

    def handle(self, *args, **options):
        self.save_page = options['save_page']
        self.stdout.write('Starting MLA scraper...')
        self.setup_driver()
        self.scrape_mlas()
        self.driver.quit()
        self.stdout.write(self.style.SUCCESS('MLA scraping completed.'))

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

    def scrape_mlas(self):
        # First, get the list of states from the main page
        url = "https://prsindia.org/mlatrack"
        self.driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        select = soup.find('select', {'name': 'state'})
        if not select:
            self.stdout.write(self.style.ERROR('Could not find state dropdown.'))
            return
        options = select.find_all('option')
        state_names = [opt.text for opt in options if opt.text != 'State' and opt.text != '']
        self.stdout.write(f'Found {len(state_names)} states.')

        # For each state, scrape its MLA page
        for state_name in state_names:
            self.stdout.write(f'Scraping MLAs for {state_name}...')
            # Encode state name for URL
            encoded_state = urllib.parse.quote(state_name)
            state_url = f"https://prsindia.org/mlatrack?state={encoded_state}"
            self.driver.get(state_url)
            time.sleep(3)
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.views-row')))
            except:
                self.stdout.write(f'  No MLAs found for {state_name}.')
                if self.save_page:
                    self.save_page_source(f'mla_{state_name}.html')
                continue

            if self.save_page:
                self.save_page_source(f'mla_{state_name}.html')
            self.parse_mla_page(state_name)

    def parse_mla_page(self, state_name):
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        rows = soup.select('div.views-row')
        if not rows:
            self.stdout.write(f'  No MLA rows found for {state_name}.')
            return

        state, _ = State.objects.get_or_create(name=state_name)
        saved = 0
        for row in rows:
            party_elem = row.select_one('.views-field-field-political-party .field-content')
            party_name = party_elem.get_text(strip=True) if party_elem else ''
            name_elem = row.select_one('.views-field-title-field h3 a')
            name = name_elem.get_text(strip=True) if name_elem else ''
            const_elem = row.select_one('.views-field-php .field-content')
            constituency = const_elem.get_text(strip=True) if const_elem else ''
            if not name:
                continue
            party, _ = Party.objects.get_or_create(name=party_name) if party_name else (None, None)
            MLA.objects.update_or_create(
                name=name,
                state=state,
                constituency=constituency,
                defaults={'party': party}
            )
            saved += 1
        self.stdout.write(f'  Saved {saved} MLAs for {state_name}.')

    def save_page_source(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        self.stdout.write(f'Saved page source to {filename}')