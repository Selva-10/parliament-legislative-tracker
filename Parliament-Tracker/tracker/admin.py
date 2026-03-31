# tracker/admin.py
from django.contrib import admin
from .models import Bill, BillUpdate, ScrapeSource, State, Party, MP, MLA

# --- Existing registrations ---
@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_id', 'title', 'house', 'status', 'introduction_date', 'source', 'state')
    list_filter = ('house', 'status', 'source', 'introduction_date')
    search_fields = ('bill_id', 'title', 'bill_number', 'introduced_by', 'state')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'introduction_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'bill_id', 'bill_number', 'title', 'short_title')
        }),
        ('House & Status', {
            'fields': ('house', 'introduced_in', 'status', 'status_details')
        }),
        ('Dates', {
            'fields': ('introduction_date', 'passed_date', 'created_at', 'updated_at')
        }),
        ('Sponsors', {
            'fields': ('introduced_by', 'introduced_by_mp', 'introduced_by_party', 'ministry')
        }),
        ('Geography', {
            'fields': ('state',)
        }),
        ('Content', {
            'fields': ('description', 'objective')
        }),
        ('Links', {
            'fields': ('prs_link', 'loksabha_link', 'rajyasabha_link', 'pdf_link')
        }),
        ('Metadata', {
            'fields': ('source', 'source_id', 'tags', 'is_active')
        }),
    )


@admin.register(BillUpdate)
class BillUpdateAdmin(admin.ModelAdmin):
    list_display = ('bill', 'update_type', 'update_date')
    list_filter = ('update_type', 'update_date')
    search_fields = ('bill__title', 'bill__bill_id', 'description')
    date_hierarchy = 'update_date'


@admin.register(ScrapeSource)
class ScrapeSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'is_active', 'last_scraped')
    list_filter = ('source_type', 'is_active')
    search_fields = ('name', 'base_url')
from .models import State, Party, MP, MLA

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')
    search_fields = ('name', 'abbreviation')

@admin.register(MP)
class MPAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'constituency', 'house', 'party')
    list_filter = ('house', 'state', 'party')
    search_fields = ('name', 'constituency')
    autocomplete_fields = ('state', 'party')

@admin.register(MLA)
class MLAAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'constituency', 'party')
    list_filter = ('state', 'party')
    search_fields = ('name', 'constituency')
    autocomplete_fields = ('state', 'party')

