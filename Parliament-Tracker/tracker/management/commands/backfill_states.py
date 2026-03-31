# tracker/management/commands/backfill_states.py
from django.core.management.base import BaseCommand
from tracker.models import Bill
import re

class Command(BaseCommand):
    help = 'Assign states to existing bills based on introducer or title'

    def handle(self, *args, **options):
        minister_state_map = {
            'Minister of Finance': 'Maharashtra',
            'Minister of Home Affairs': 'Delhi',
            'Minister of Defence': 'Uttar Pradesh',
            'Minister of External Affairs': 'Delhi',
            'Minister of Law and Justice': 'West Bengal',
            'Minister of Electronics and IT': 'Karnataka',
            'Minister of Science and Technology': 'Tamil Nadu',
            'Minister of Ports and Shipping': 'Gujarat',
            'Minister of Labour and Employment': 'Bihar',
            'Minister of Health': 'Madhya Pradesh',
            'Minister of Education': 'Rajasthan',
            'Minister of Agriculture': 'Punjab',
            'Minister of Railways': 'Odisha',
            'Minister of Coal': 'Jharkhand',
            'Minister of Petroleum': 'Assam',
            'Minister of Steel': 'Jharkhand',
            'Minister of Textiles': 'Gujarat',
            'Minister of Commerce': 'Tamil Nadu',
            'Minister of Jal Shakti': 'Uttar Pradesh',
            'Minister of Space': 'Karnataka',
            'Chairman of Rajya Sabha': 'Delhi',
        }
        
        title_state_keywords = {
            'delhi': 'Delhi',
            'mumbai': 'Maharashtra',
            'maharashtra': 'Maharashtra',
            'chennai': 'Tamil Nadu',
            'tamil nadu': 'Tamil Nadu',
            'kolkata': 'West Bengal',
            'west bengal': 'West Bengal',
            'bangalore': 'Karnataka',
            'karnataka': 'Karnataka',
            'hyderabad': 'Telangana',
            'telangana': 'Telangana',
            'ahmedabad': 'Gujarat',
            'gujarat': 'Gujarat',
            'lucknow': 'Uttar Pradesh',
            'patna': 'Bihar',
            'bhopal': 'Madhya Pradesh',
            'jaipur': 'Rajasthan',
            'chandigarh': 'Punjab',
        }

        updated = 0
        for bill in Bill.objects.filter(state=''):
            state = None
            introducer = bill.introduced_by or ''
            for minister, st in minister_state_map.items():
                if minister.lower() in introducer.lower():
                    state = st
                    break
            if not state and bill.title:
                title_lower = bill.title.lower()
                for kw, st in title_state_keywords.items():
                    if kw in title_lower:
                        state = st
                        break
            if not state:
                state = 'Other'
            
            bill.state = state
            bill.save()
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Updated {updated} bills with state information'))