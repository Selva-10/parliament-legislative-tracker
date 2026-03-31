# tracker/management/commands/import_from_html.py
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup
from tracker.models import State, Party, MP, MLA
import os

class Command(BaseCommand):
    help = 'Import MPs and MLAs from saved HTML files (mp_track.html, mla_track.html)'

    def add_arguments(self, parser):
        parser.add_argument('--mp-file', type=str, default='mp_track.html')
        parser.add_argument('--mla-file', type=str, default='mla_track.html')
        parser.add_argument('--mp-row-selector', type=str, help='CSS selector for MP rows')
        parser.add_argument('--mp-name-selector', type=str, help='CSS selector for MP name')
        parser.add_argument('--mp-const-selector', type=str, help='CSS selector for MP constituency')
        parser.add_argument('--mp-state-selector', type=str, help='CSS selector for MP state')
        parser.add_argument('--mp-party-selector', type=str, help='CSS selector for MP party')
        parser.add_argument('--mp-house-selector', type=str, help='CSS selector for MP house (optional)')
        parser.add_argument('--mla-row-selector', type=str, help='CSS selector for MLA rows')
        parser.add_argument('--mla-name-selector', type=str, help='CSS selector for MLA name')
        parser.add_argument('--mla-const-selector', type=str, help='CSS selector for MLA constituency')
        parser.add_argument('--mla-state-selector', type=str, help='CSS selector for MLA state')
        parser.add_argument('--mla-party-selector', type=str, help='CSS selector for MLA party')
        parser.add_argument('--debug', action='store_true', help='Print HTML preview for debugging')

    def handle(self, *args, **options):
        mp_file = options['mp_file']
        mla_file = options['mla_file']
        debug = options['debug']

        if os.path.exists(mp_file):
            self.import_mp(mp_file, options, debug)
        else:
            self.stdout.write(self.style.WARNING(f'MP file not found: {mp_file}'))

        if os.path.exists(mla_file):
            self.import_mla(mla_file, options, debug)
        else:
            self.stdout.write(self.style.WARNING(f'MLA file not found: {mla_file}'))

    def import_mp(self, filepath, options, debug):
        self.stdout.write(f'Importing MPs from {filepath}')
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        row_selector = options['mp_row_selector'] or 'div.views-row, table tbody tr, .views-row'
        name_selector = options['mp_name_selector'] or '.views-field-title a, .field-content a, .mp-name a, h3 a'
        const_selector = options['mp_const_selector'] or '.views-field-field-constituency .field-content, .mp-constituency'
        state_selector = options['mp_state_selector'] or '.views-field-field-state .field-content, .mp-state'
        party_selector = options['mp_party_selector'] or '.views-field-field-party .field-content, .mp-party'
        house_selector = options['mp_house_selector'] or None

        rows = soup.select(row_selector)
        if not rows:
            self.stdout.write(self.style.ERROR('No MP rows found with given selectors.'))
            if debug:
                self.stdout.write(soup.prettify()[:3000])
            return

        self.stdout.write(f'Found {len(rows)} rows.')

        for idx, row in enumerate(rows):
            # Try to get name from row using the selector
            name_elem = row.select_one(name_selector)
            if not name_elem:
                # Fallback: if row is a table row, try td[0]
                tds = row.find_all('td')
                if len(tds) >= 4:
                    name = tds[0].get_text(strip=True)
                    constituency = tds[1].get_text(strip=True)
                    state_name = tds[2].get_text(strip=True)
                    party_name = tds[3].get_text(strip=True)
                else:
                    continue
            else:
                name = name_elem.get_text(strip=True)
                # Extract other fields
                const_elem = row.select_one(const_selector)
                constituency = const_elem.get_text(strip=True) if const_elem else ''
                state_elem = row.select_one(state_selector)
                state_name = state_elem.get_text(strip=True) if state_elem else ''
                party_elem = row.select_one(party_selector)
                party_name = party_elem.get_text(strip=True) if party_elem else ''

            if not name:
                continue

            state = State.objects.get_or_create(name=state_name)[0] if state_name else None
            party = Party.objects.get_or_create(name=party_name)[0] if party_name else None
            house = 'LOK_SABHA'  # default
            if house_selector:
                house_elem = row.select_one(house_selector)
                if house_elem:
                    house_text = house_elem.get_text(strip=True).lower()
                    if 'rajya' in house_text:
                        house = 'RAJYA_SABHA'

            MP.objects.update_or_create(
                name=name,
                state=state,
                constituency=constituency,
                defaults={'house': house, 'party': party}
            )
            self.stdout.write(f'Saved MP: {name}')

        self.stdout.write(self.style.SUCCESS('MP import completed.'))

    def import_mla(self, filepath, options, debug):
        self.stdout.write(f'Importing MLAs from {filepath}')
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        row_selector = options['mla_row_selector'] or 'div.views-row, table tbody tr, .views-row, .mla-list-item'
        name_selector = options['mla_name_selector'] or '.views-field-title a, .field-content a, .mla-name a, h3 a'
        const_selector = options['mla_const_selector'] or '.views-field-field-constituency .field-content, .mla-constituency'
        state_selector = options['mla_state_selector'] or '.views-field-field-state .field-content, .mla-state'
        party_selector = options['mla_party_selector'] or '.views-field-field-party .field-content, .mla-party'

        rows = soup.select(row_selector)
        if not rows:
            self.stdout.write(self.style.ERROR('No MLA rows found with given selectors.'))
            if debug:
                self.stdout.write('First 3000 characters of page:')
                self.stdout.write(soup.prettify()[:3000])
            return

        self.stdout.write(f'Found {len(rows)} rows.')

        for idx, row in enumerate(rows):
            name_elem = row.select_one(name_selector)
            if not name_elem:
                tds = row.find_all('td')
                if len(tds) >= 4:
                    name = tds[0].get_text(strip=True)
                    constituency = tds[1].get_text(strip=True)
                    state_name = tds[2].get_text(strip=True)
                    party_name = tds[3].get_text(strip=True)
                else:
                    continue
            else:
                name = name_elem.get_text(strip=True)
                const_elem = row.select_one(const_selector)
                constituency = const_elem.get_text(strip=True) if const_elem else ''
                state_elem = row.select_one(state_selector)
                state_name = state_elem.get_text(strip=True) if state_elem else ''
                party_elem = row.select_one(party_selector)
                party_name = party_elem.get_text(strip=True) if party_elem else ''

            if not name:
                continue

            state = State.objects.get_or_create(name=state_name)[0] if state_name else None
            party = Party.objects.get_or_create(name=party_name)[0] if party_name else None

            MLA.objects.update_or_create(
                name=name,
                state=state,
                constituency=constituency,
                defaults={'party': party}
            )
            self.stdout.write(f'Saved MLA: {name}')

        self.stdout.write(self.style.SUCCESS('MLA import completed.'))