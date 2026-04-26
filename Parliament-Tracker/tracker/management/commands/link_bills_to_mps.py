# tracker/management/commands/link_bills_to_mps.py
from django.core.management.base import BaseCommand
from tracker.models import Bill, MP
import re

class Command(BaseCommand):
    help = 'Link bills to MPs based on introduced_by name'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("LINKING BILLS TO MPS")
        self.stdout.write("=" * 60)

        def normalize_name(name):
            """Extract clean name without titles"""
            if not name:
                return ""
            
            titles = ['Shri', 'Smt', 'Dr', 'Prof', 'Shrimati', 'Shri.', 'Smt.', 'Dr.', 'Mr.', 'Ms.', 'M/s']
            for title in titles:
                name = re.sub(rf'^{title}\s+', '', name, flags=re.IGNORECASE)
                name = re.sub(rf'\s+{title}\s+', ' ', name, flags=re.IGNORECASE)
            
            name = re.sub(r'\([^)]*\)', '', name)
            name = ' '.join(name.split())
            return name.strip()

        # Get all MPs
        mps = list(MP.objects.select_related('party').all())
        self.stdout.write(f"📋 Found {len(mps)} MPs in database")

        # Create search index
        mp_index = {}
        for mp in mps:
            clean_name = normalize_name(mp.name)
            mp_index[clean_name.lower()] = mp
            mp_index[mp.name.lower()] = mp
            
            last_name = clean_name.split()[-1] if clean_name.split() else ''
            if last_name and len(last_name) > 3:
                if last_name.lower() not in mp_index:
                    mp_index[last_name.lower()] = mp

        # Get bills without MP linkage
        bills = Bill.objects.filter(introduced_by_mp__isnull=True, introduced_by__isnull=False).exclude(introduced_by='')
        self.stdout.write(f"📋 Found {bills.count()} bills to link")

        matched = 0
        unmatched = []

        for bill in bills:
            if not bill.introduced_by:
                continue
            
            clean_name = normalize_name(bill.introduced_by)
            matched_mp = None
            
            if clean_name.lower() in mp_index:
                matched_mp = mp_index[clean_name.lower()]
            
            if not matched_mp and clean_name:
                last_name = clean_name.split()[-1]
                if last_name and len(last_name) > 3 and last_name.lower() in mp_index:
                    matched_mp = mp_index[last_name.lower()]
            
            if not matched_mp and clean_name:
                for mp in mps:
                    mp_clean = normalize_name(mp.name)
                    if (clean_name.lower() in mp_clean.lower() or 
                        mp_clean.lower() in clean_name.lower()):
                        matched_mp = mp
                        break
            
            if matched_mp:
                bill.introduced_by_mp = matched_mp
                bill.introduced_by_party = matched_mp.party.abbreviation if matched_mp.party else ''
                bill.save()
                matched += 1
                self.stdout.write(f"  ✓ {bill.title[:50]} -> {matched_mp.name} ({bill.introduced_by_party})")
            else:
                unmatched.append((bill.title[:50], bill.introduced_by))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"✅ MATCHED: {matched} bills")
        self.stdout.write(f"❌ UNMATCHED: {len(unmatched)} bills")
        
        if unmatched:
            self.stdout.write("\n⚠️ Unmatched introducers (need manual mapping):")
            for title, name in unmatched[:20]:
                self.stdout.write(f"  - '{name}' (Bill: {title})")