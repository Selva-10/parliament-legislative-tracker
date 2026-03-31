# tracker/management/commands/generate_historical_bills.py
from django.core.management.base import BaseCommand
from tracker.models import Bill
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Generate realistic historical bills from the past year'

    def handle(self, *args, **options):
        today = date.today()
        start_date = today - timedelta(days=365)
        
        ministers = [
            ('Nirmala Sitharaman', 'BJP', 'Ministry of Finance', 'Maharashtra'),
            ('Amit Shah', 'BJP', 'Ministry of Home Affairs', 'Delhi'),
            ('Rajnath Singh', 'BJP', 'Ministry of Defence', 'Uttar Pradesh'),
            ('Dharmendra Pradhan', 'BJP', 'Ministry of Education', 'Rajasthan'),
            ('Mansukh Mandaviya', 'BJP', 'Ministry of Health', 'Madhya Pradesh'),
            ('Kiren Rijiju', 'BJP', 'Ministry of Law and Justice', 'West Bengal'),
            ('Piyush Goyal', 'BJP', 'Ministry of Commerce', 'Gujarat'),
            ('Gajendra Singh Shekhawat', 'BJP', 'Ministry of Jal Shakti', 'Uttar Pradesh'),
            ('Ashwini Vaishnaw', 'BJP', 'Ministry of Electronics and IT', 'Karnataka'),
            ('Jitendra Singh', 'BJP', 'Ministry of Space', 'Karnataka'),
        ]

        houses = ['LOK_SABHA', 'RAJYA_SABHA']
        statuses = ['PASSED', 'PENDING', 'REJECTED']

        bills_created = 0
        for i in range(100):
            intro_date = start_date + timedelta(days=random.randint(0, 365))
            year = intro_date.year
            bill_id = f"BILL-{intro_date.strftime('%Y%m%d')}-{i+1:03d}"
            
            minister, party, ministry, state = random.choice(ministers)
            house = random.choice(houses)
            status = random.choice(statuses)
            passed_date = intro_date + timedelta(days=random.randint(30, 180)) if status == 'PASSED' else None

            bill, created = Bill.objects.update_or_create(
                bill_id=bill_id,
                defaults={
                    'bill_number': f'{random.randint(1,500)} of {year}',
                    'title': f'The {ministry.replace("Ministry of ","")} (Amendment) Bill, {year}',
                    'house': house,
                    'status': status,
                    'introduction_date': intro_date,
                    'passed_date': passed_date,
                    'introduced_by': minister,
                    'introduced_by_party': party,
                    'ministry': ministry,
                    'state': state,
                    'source': 'HISTORICAL'
                }
            )
            if created:
                bills_created += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Generated {bills_created} historical bills'))