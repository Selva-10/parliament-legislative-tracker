# tracker/management/commands/fix_houses.py
from django.core.management.base import BaseCommand
from tracker.models import Bill
import re

class Command(BaseCommand):
    help = 'Fix house assignments for bills based on title analysis'

    def handle(self, *args, **options):
        self.stdout.write("Fixing house assignments...")
        
        # Rajya Sabha indicators
        rs_indicators = [
            'rajya sabha', 'राज्यसभा', 'council of states',
            'rs ', ' (rs) ', 'rajya sabha', 'राज्य सभा',
            'parliament of india - council of states'
        ]
        
        # Lok Sabha indicators
        ls_indicators = [
            'lok sabha', 'लोकसभा', 'house of the people',
            'ls ', ' (ls) ', 'lok sabha', 'लोक सभा'
        ]
        
        # Update Rajya Sabha bills
        rs_count = 0
        for bill in Bill.objects.all():
            title_lower = bill.title.lower()
            ministry_lower = (bill.ministry or '').lower()
            
            # Check if it should be Rajya Sabha
            should_be_rs = False
            for ind in rs_indicators:
                if ind in title_lower or ind in ministry_lower:
                    should_be_rs = True
                    break
            
            if should_be_rs and bill.house != 'RAJYA_SABHA':
                bill.house = 'RAJYA_SABHA'
                bill.save()
                rs_count += 1
                self.stdout.write(f"✅ Updated {bill.bill_id} to Rajya Sabha")
        
        # Update Lok Sabha bills (optional - uncomment if needed)
        # ls_count = 0
        # for bill in Bill.objects.filter(house='RAJYA_SABHA'):
        #     title_lower = bill.title.lower()
        #     for ind in ls_indicators:
        #         if ind in title_lower:
        #             bill.house = 'LOK_SABHA'
        #             bill.save()
        #             ls_count += 1
        #             break
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Updated {rs_count} bills to Rajya Sabha"))
        
        # Count final results
        total_rs = Bill.objects.filter(house='RAJYA_SABHA').count()
        total_ls = Bill.objects.filter(house='LOK_SABHA').count()
        total_bills = Bill.objects.count()
        
        self.stdout.write(self.style.SUCCESS(
            f"\nFinal count:\n"
            f"  Lok Sabha: {total_ls} bills\n"
            f"  Rajya Sabha: {total_rs} bills\n"
            f"  Total: {total_bills} bills"
        ))