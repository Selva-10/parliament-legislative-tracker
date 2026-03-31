from rest_framework import serializers
from .models import Bill, MemberOfParliament, State, CalendarEvent

class BillSerializer(serializers.ModelSerializer):
    ministry_name = serializers.CharField(source='ministry.name')
    introduced_by_name = serializers.CharField(source='introduced_by.name')
    class Meta:
        model = Bill
        fields = ['id','bill_id','title','short_title','bill_type','status','introduced_date','last_action_date','passing_date','ministry_name','introduced_by_name','summary','keywords','success_probability','days_since_introduction']

class MemberOfParliamentSerializer(serializers.ModelSerializer):
    party_name = serializers.CharField(source='party.name')
    class Meta:
        model = MemberOfParliament
        fields = ['id','name','house','constituency','state','party_name','total_bills_introduced','total_bills_passed','attendance_percentage','questions_asked']

class StateSerializer(serializers.ModelSerializer):
    ruling_party_name = serializers.CharField(source='ruling_party.name')
    class Meta:
        model = State
        fields = ['id','name','state_code','capital','ruling_party_name','bills_introduced','bills_passed','total_mps','latitude','longitude']

class CalendarEventSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_event_category_display')
    bill_title = serializers.CharField(source='bill.short_title')
    class Meta:
        model = CalendarEvent
        fields = ['id','title','start_datetime','end_datetime','event_category','category_display','priority','location','status','bill_title','virtual_link']