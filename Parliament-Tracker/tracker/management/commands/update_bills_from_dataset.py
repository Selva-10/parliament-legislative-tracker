import json
import requests
from django.core.management.base import BaseCommand
from tracker.models import Bill

class Command(BaseCommand):
    help = 'Update bill introducer and party using the india-representatives-activity dataset'

    def handle(self, *args, **options):
        self.stdout.write("Downloading dataset from GitHub...")
        url = "https://raw.githubusercontent.com/Vonter/india-representatives-activity/main/json/Lok%20Sabha/18th.json"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to download dataset: {e}"))
            return

        # Build mapping: bill title -> (member name, party)
        bill_map = {}
        for member in data:
            member_name = member.get("Name")
            party = member.get("Party")
            if not member_name or not party:
                continue

            bills_data = member.get("Private Member Bills")
            # If it's not a list (e.g., 0 or None), skip
            if not isinstance(bills_data, list):
                continue

            for bill_item in bills_data:
                # If the bill item is a dictionary, extract the title
                title = None
                if isinstance(bill_item, dict):
                    # Try common keys for the title
                    title = bill_item.get("Title") or bill_item.get("title") or bill_item.get("Bill Title") or bill_item.get("bill_title")
                elif isinstance(bill_item, str):
                    title = bill_item

                if title:
                    # Normalize whitespace
                    title = ' '.join(title.split())
                    bill_map[title] = (member_name, party)

        self.stdout.write(f"Loaded {len(bill_map)} unique bill titles from dataset.")

        updated = 0
        not_found = 0
        bills = Bill.objects.all()
        for bill in bills:
            # Normalize bill title for matching
            title = ' '.join(bill.title.split())
            if title in bill_map:
                introducer, party = bill_map[title]
                # Only update if fields are currently empty
                if not bill.introduced_by or not bill.introduced_by_party:
                    bill.introduced_by = introducer
                    bill.introduced_by_party = party
                    bill.save()
                    updated += 1
                    self.stdout.write(f"Updated {bill.bill_id}: {introducer} ({party})")
            else:
                not_found += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} bills. {not_found} bills not found in dataset."))