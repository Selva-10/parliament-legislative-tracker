# tracker/management/commands/import_datagov_bills.py
import csv
from django.core.management.base import BaseCommand
from tracker.models import Bill
from datetime import datetime
import re
import os

class Command(BaseCommand):
    help = 'Import bills from data.gov.in CSV with all columns'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to downloaded CSV file')
        parser.add_argument('--clear', action='store_true', help='Clear existing bills before import')
        parser.add_argument('--source', type=str, default='DATA_GOV_IN', help='Source label for imported bills')

    def _parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str or date_str.strip() == '':
            return None
        
        date_str = str(date_str).strip()
        
        # Remove common prefixes
        date_str = re.sub(r'(Dated|dt\.|Date:)', '', date_str, flags=re.IGNORECASE)
        date_str = date_str.strip()
        
        # Try DD/MM/YYYY format (most common in Indian data)
        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
        if date_match:
            try:
                day, month, year = date_match.groups()
                return datetime(int(year), int(month), int(day)).date()
            except ValueError:
                pass
        
        # Try other formats
        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', 
            '%d %B %Y', '%B %d, %Y', '%d %b %Y',
            '%b %d, %Y', '%d.%m.%Y'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None

    def _extract_year(self, date_obj):
        """Extract year from date object"""
        return date_obj.year if date_obj else None

    def handle(self, *args, **options):
        csv_path = options['csv_file']
        clear_existing = options['clear']
        source = options['source']
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"File not found: {csv_path}"))
            return
        
        if clear_existing:
            count = Bill.objects.filter(source=source).count()
            Bill.objects.filter(source=source).delete()
            self.stdout.write(f"Cleared {count} existing bills from source: {source}")
        
        self.stdout.write(f"Importing bills from {csv_path}")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Detect delimiter
            sample = f.read(1024)
            f.seek(0)
            delimiter = ',' if ',' in sample else '\t'
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Map CSV headers to model fields (adjust based on actual CSV)
            # Common column names from data.gov.in
            field_mapping = {
                'year': ['year', 'Year', 'YEAR'],
                'bill_number': ['bill_number', 'Bill number', 'Bill Number', 'BILL_NO'],
                'title': ['title_of_the_bill', 'Title of the bill', 'Title', 'TITLE'],
                'introduction_date': ['date_of_introduction', 'Introduction Date', 'INTRO_DATE'],
                'passed_ls_date': ['debate_passed_in_loksabha', 'Debate / passed in Loksabha', 'LS_PASSED', 'LOK_SABHA_DATE'],
                'passed_rs_date': ['debate_passed_in_rajyasabha', 'Debate / passed in Rajya Sabha', 'RS_PASSED', 'RAJYA_SABHA_DATE'],
                'committee_ref': ['referred_to_committee_report_presented', 'Committee Reference', 'COMMITTEE_DATE'],
                'assent_date': ['assent_date_gazette_notification', 'Assent date', 'ASENT_DATE', 'GAZETTE_DATE'],
                'bill_type': ['type_of_bill', 'Bill Type', 'TYPE', 'government_private'],
                'ministry': ['ministry_department', 'Ministry', 'Department', 'MINISTRY'],
                'originating_house': ['originating_house', 'House', 'ORIGIN'],
            }
            
            def get_field_value(row, possible_keys):
                for key in possible_keys:
                    if key in row:
                        val = row[key]
                        if val and str(val).strip():
                            return str(val).strip()
                return ''
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for row in reader:
                try:
                    # Extract values
                    title = get_field_value(row, field_mapping['title'])
                    if not title:
                        skipped_count += 1
                        continue
                    
                    bill_number = get_field_value(row, field_mapping['bill_number'])
                    
                    # Parse dates
                    intro_date = self._parse_date(get_field_value(row, field_mapping['introduction_date']))
                    passed_ls_date = self._parse_date(get_field_value(row, field_mapping['passed_ls_date']))
                    passed_rs_date = self._parse_date(get_field_value(row, field_mapping['passed_rs_date']))
                    assent_date = self._parse_date(get_field_value(row, field_mapping['assent_date']))
                    
                    # Committee reference date
                    committee_date_str = get_field_value(row, field_mapping['committee_ref'])
                    committee_report_date = self._parse_date(committee_date_str) if committee_date_str else None
                    
                    # Other fields
                    bill_type = get_field_value(row, field_mapping['bill_type'])
                    ministry = get_field_value(row, field_mapping['ministry'])
                    year_str = get_field_value(row, field_mapping['year'])
                    originating_house = get_field_value(row, field_mapping['originating_house'])
                    
                    # Determine status
                    if assent_date:
                        status = 'PASSED'
                    elif passed_ls_date and passed_rs_date:
                        status = 'PASSED'
                    elif passed_ls_date or passed_rs_date:
                        status = 'PASSED'
                    else:
                        status = 'PENDING'
                    
                    # Determine house
                    if passed_ls_date and passed_rs_date:
                        house = 'BOTH'
                    elif passed_ls_date:
                        house = 'LOK_SABHA'
                    elif passed_rs_date:
                        house = 'RAJYA_SABHA'
                    else:
                        house = originating_house if originating_house in ['LOK_SABHA', 'RAJYA_SABHA'] else 'LOK_SABHA'
                    
                    # Generate unique bill ID
                    year = int(year_str) if year_str and year_str.isdigit() else (intro_date.year if intro_date else 0)
                    bill_id = f"{source}-{year}-{bill_number}" if bill_number else f"{source}-{abs(hash(title)) % 10000:04d}"
                    
                    # Check if committee was referred
                    referred_to_committee = committee_report_date is not None
                    
                    # Create or update bill
                    obj, created = Bill.objects.update_or_create(
                        bill_id=bill_id,
                        defaults={
                            'bill_number': bill_number,
                            'title': title,
                            'bill_type': bill_type,
                            'introduction_date': intro_date,
                            'passed_in_ls_date': passed_ls_date,
                            'passed_in_rs_date': passed_rs_date,
                            'debated_on_ls_date': passed_ls_date,
                            'debated_on_rs_date': passed_rs_date,
                            'assent_date': assent_date,
                            'committee_report_date': committee_report_date,
                            'referred_to_committee': referred_to_committee,
                            'originating_house': house,
                            'legislative_year': year,
                            'ministry': ministry,
                            'house': house,
                            'status': status,
                            'source': source,
                            'passed_date': passed_ls_date or passed_rs_date or assent_date,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        if passed_ls_date or passed_rs_date:
                            self.stdout.write(f"  ✓ {title[:50]} | LS: {passed_ls_date} | RS: {passed_rs_date} | Assent: {assent_date}")
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing row: {e}"))
                    skipped_count += 1
            
            # Final summary
            self.stdout.write(self.style.SUCCESS(f"\n✅ IMPORT COMPLETE!"))
            self.stdout.write(f"   Created: {created_count}")
            self.stdout.write(f"   Updated: {updated_count}")
            self.stdout.write(f"   Skipped: {skipped_count}")
            
            # Show statistics
            total = Bill.objects.filter(source=source).count()
            with_ls = Bill.objects.filter(passed_in_ls_date__isnull=False, source=source).count()
            with_rs = Bill.objects.filter(passed_in_rs_date__isnull=False, source=source).count()
            with_assent = Bill.objects.filter(assent_date__isnull=False, source=source).count()
            
            self.stdout.write(f"\n📊 IMPORT STATISTICS:")
            self.stdout.write(f"   Total bills: {total}")
            self.stdout.write(f"   With LS passed date: {with_ls}")
            self.stdout.write(f"   With RS passed date: {with_rs}")
            self.stdout.write(f"   Received Presidential Assent: {with_assent}")