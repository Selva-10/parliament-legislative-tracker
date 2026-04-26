# tracker/admin.py
from django.contrib import admin
from .models import Bill, MP, MLA, State, Party, BillUpdate, ScrapeSource

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = [
        'bill_id', 
        'bill_number', 
        'title', 
        'house', 
        'status', 
        'introduction_date',
        'introduced_by',
        'introduced_by_party',
        'source',
        'last_updated'
    ]
    list_filter = ['status', 'house', 'source', 'introduction_date']
    search_fields = ['bill_id', 'title', 'introduced_by', 'short_title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-introduction_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('bill_id', 'bill_number', 'bill_number_display', 'title', 'short_title', 'bill_type')
        }),
        ('House & Origin', {
            'fields': ('house', 'originating_house')
        }),
        ('Dates', {
            'fields': ('introduction_date', 'legislative_year', 'passed_in_ls_date', 'passed_in_rs_date')
        }),
        ('Committee & Assent', {
            'fields': ('referred_to_committee_date', 'committee_name', 'committee_report_date', 'assent_date', 'act_number', 'gazette_notification_date', 'gazette_notification_number')
        }),
        ('Members', {
            'fields': ('introduced_by', 'introduced_by_mp', 'introduced_by_party', 'member_name')
        }),
        ('Ministry & Status', {
            'fields': ('ministry', 'status', 'status_display', 'status_history')
        }),
        ('Description', {
            'fields': ('description', 'objective')
        }),
        ('Links', {
            'fields': ('prs_link', 'sansad_link', 'loksabha_link', 'rajyasabha_link', 'pdf_link')
        }),
        ('Metadata', {
            'fields': ('source', 'source_id', 'tags', 'is_active', 'is_government_bill', 'bill_year', 'bill_series')
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at', 'last_updated')
        }),
    )

@admin.register(MP)
class MPAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'constituency', 'house', 'party']
    list_filter = ['house', 'state', 'party']
    search_fields = ['name', 'constituency']

@admin.register(MLA)
class MLAAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'constituency', 'party']
    list_filter = ['state', 'party']
    search_fields = ['name', 'constituency']

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name']

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbreviation']
    search_fields = ['name', 'abbreviation']

@admin.register(BillUpdate)
class BillUpdateAdmin(admin.ModelAdmin):
    list_display = ['bill', 'update_date', 'update_type']
    list_filter = ['update_type', 'update_date']

@admin.register(ScrapeSource)
class ScrapeSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'is_active', 'last_scraped']
    list_filter = ['source_type', 'is_active']