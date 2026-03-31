# tracker/management/commands/fix_bill_details.py
from django.core.management.base import BaseCommand
from tracker.models import Bill
import re

class Command(BaseCommand):
    help = 'Fix bill numbers and introducers based on title patterns'

    def handle(self, *args, **options):
        bills = Bill.objects.all()
        updated = 0
        for bill in bills:
            changed = False
            # Extract bill number
            bill_number = self.extract_bill_number(bill.title)
            if bill_number and bill_number != bill.bill_number:
                bill.bill_number = bill_number
                changed = True
            # Extract introducer
            introducer = self.extract_introducer(bill.title)
            if introducer and introducer != bill.introduced_by:
                bill.introduced_by = introducer
                changed = True
            if changed:
                bill.save()
                updated += 1
                self.stdout.write(f"Updated {bill.bill_id}: {bill.bill_number} - {bill.introduced_by}")
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} bills"))

    def extract_bill_number(self, title):
        # Pattern for "No.2" or "(No.2)" or "Bill No. 123"
        patterns = [
            r'No\.?\s*(\d+)',
            r'\(No\.?\s*(\d+)\)',
            r'Bill\s+No\.?\s*(\d+)',
            r'(\d+)(?:st|nd|rd|th)?\s+Bill',
        ]
        for pat in patterns:
            m = re.search(pat, title, re.IGNORECASE)
            if m:
                num = m.group(1)
                year_match = re.search(r'20\d{2}', title)
                year = year_match.group() if year_match else ''
                if year:
                    return f"{num} of {year}"
                return num
        return ''

    def extract_introducer(self, title):
        title_lower = title.lower()
        if 'finance' in title_lower or 'appropriation' in title_lower:
            return 'Minister of Finance'
        if 'home' in title_lower or 'nagarik' in title_lower or 'internal' in title_lower:
            return 'Minister of Home Affairs'
        if 'law' in title_lower or 'justice' in title_lower or 'nyaya' in title_lower or 'arbitration' in title_lower:
            return 'Minister of Law and Justice'
        if 'labour' in title_lower or 'wages' in title_lower or 'employment' in title_lower:
            return 'Minister of Labour and Employment'
        if 'defence' in title_lower or 'defense' in title_lower:
            return 'Minister of Defence'
        if 'education' in title_lower:
            return 'Minister of Education'
        if 'health' in title_lower:
            return 'Minister of Health and Family Welfare'
        return 'Minister Concerned'