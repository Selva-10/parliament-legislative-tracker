# tracker/models.py
from django.db import models
from django.utils import timezone
import uuid

class Bill(models.Model):
    """Bill model with all necessary fields for Sansad website data"""
    
    BILL_STATUS = [
        ('PENDING', 'Pending'),
        ('PASSED', 'Passed'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
        ('LAPSED', 'Lapsed'),
        ('ENACTED', 'Enacted'),
    ]
    
    HOUSE_CHOICES = [
        ('LOK_SABHA', 'Lok Sabha'),
        ('RAJYA_SABHA', 'Rajya Sabha'),
        ('BOTH', 'Both Houses'),
    ]
    
    BILL_TYPE_CHOICES = [
        ('GOVERNMENT', 'Government Bill'),
        ('PRIVATE', 'Private Member Bill'),
        ('FINANCE', 'Finance Bill'),
        ('CONSTITUTION', 'Constitution Amendment Bill'),
    ]
    
    ORIGIN_CHOICES = [
        ('LOK_SABHA', 'Lok Sabha'),
        ('RAJYA_SABHA', 'Rajya Sabha'),
    ]
    
    # ========== BASIC INFORMATION ==========
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill_id = models.CharField(max_length=50, unique=True, help_text="Unique bill identifier")
    bill_number = models.CharField(max_length=50, blank=True, null=True)
    bill_number_display = models.CharField(max_length=50, blank=True, help_text="Bill number as displayed (e.g., Bill No. 1 of 2026)")
    title = models.CharField(max_length=500)
    short_title = models.CharField(max_length=200, blank=True, help_text="Short title of the bill")
    bill_type = models.CharField(max_length=50, choices=BILL_TYPE_CHOICES, blank=True)
    
    # ========== HOUSE INFORMATION ==========
    house = models.CharField(max_length=20, choices=HOUSE_CHOICES, default='LOK_SABHA')
    originating_house = models.CharField(max_length=20, choices=ORIGIN_CHOICES, blank=True, help_text="House where bill was first introduced")
    
    # ========== DATES (Complete as per Sansad website) ==========
    introduction_date = models.DateField(null=True, blank=True, help_text="Date of Introduction")
    legislative_year = models.IntegerField(null=True, blank=True)
    
    # Passed dates
    passed_in_ls_date = models.DateField(null=True, blank=True, verbose_name="Debate/Date Passed in Lok Sabha")
    passed_in_rs_date = models.DateField(null=True, blank=True, verbose_name="Debate/Date Passed in Rajya Sabha")
    
    # Committee details
    referred_to_committee_date = models.DateField(null=True, blank=True, help_text="Date referred to committee")
    committee_name = models.CharField(max_length=500, blank=True, help_text="Name of the committee")
    committee_report_date = models.DateField(null=True, blank=True, help_text="Date of committee report")
    
    # Presidential Assent and Gazette
    assent_date = models.DateField(null=True, blank=True, verbose_name="Assent Date")
    act_number = models.CharField(max_length=50, blank=True, help_text="Act number after presidential assent")
    gazette_notification_date = models.DateField(null=True, blank=True, verbose_name="Gazette Notification Date")
    gazette_notification_number = models.CharField(max_length=100, blank=True)
    
    # ========== MEMBERS INFORMATION ==========
    introduced_by = models.CharField(max_length=500, blank=True)
    introduced_by_mp = models.ForeignKey('MP', on_delete=models.SET_NULL, null=True, blank=True, related_name='bills_introduced')
    introduced_by_party = models.CharField(max_length=100, blank=True)
    member_name = models.CharField(max_length=200, blank=True, help_text="Member who introduced the bill (from Sansad data)")
    
    # ========== MINISTRY ==========
    ministry = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    
    # ========== STATUS ==========
    status = models.CharField(max_length=20, choices=BILL_STATUS, default='PENDING')
    status_display = models.CharField(max_length=100, blank=True, help_text="Status as displayed on Sansad website")
    status_history = models.JSONField(default=list, blank=True)
    
    # ========== DESCRIPTION ==========
    description = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    
    # ========== LINKS ==========
    prs_link = models.URLField(max_length=500, blank=True)
    sansad_link = models.URLField(max_length=500, blank=True, help_text="Link to Sansad website bill page")
    loksabha_link = models.URLField(max_length=500, blank=True)
    rajyasabha_link = models.URLField(max_length=500, blank=True)
    pdf_link = models.URLField(max_length=500, blank=True)
    
    # ========== METADATA ==========
    source = models.CharField(max_length=50, default='SANSAD')
    source_id = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # ========== ADDITIONAL SANDS SPECIFIC FIELDS ==========
    bill_year = models.IntegerField(null=True, blank=True, help_text="Year from bill number (e.g., 2026 from Bill No. 1 of 2026)")
    bill_series = models.CharField(max_length=20, blank=True, help_text="Bill series (e.g., C, G, P)")
    is_government_bill = models.BooleanField(default=True, help_text="True for Government Bill, False for Private Member Bill")
    
    # ========== TRACKING ==========
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-introduction_date', 'title']
        indexes = [
            models.Index(fields=['bill_id']),
            models.Index(fields=['house']),
            models.Index(fields=['status']),
            models.Index(fields=['introduction_date']),
            models.Index(fields=['passed_in_ls_date']),
            models.Index(fields=['passed_in_rs_date']),
            models.Index(fields=['assent_date']),
            models.Index(fields=['originating_house']),
            models.Index(fields=['bill_number']),
            models.Index(fields=['introduced_by_mp']),
        ]
    
    def __str__(self):
        return f"{self.bill_id} - {self.title[:50]}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('bill_detail', args=[str(self.id)])
    
    @property
    def status_color(self):
        colors = {
            'PENDING': 'warning',
            'PASSED': 'success',
            'REJECTED': 'danger',
            'WITHDRAWN': 'secondary',
            'LAPSED': 'dark',
            'ENACTED': 'primary',
        }
        return colors.get(self.status, 'info')
    
    @property
    def passed_both_houses(self):
        """Check if passed in both houses"""
        return self.passed_in_ls_date is not None and self.passed_in_rs_date is not None
    
    @property
    def is_enacted(self):
        """Check if bill received presidential assent"""
        return self.assent_date is not None
    
    @property
    def legislative_summary(self):
        """Get summary of bill's legislative journey"""
        summary = []
        if self.introduction_date:
            summary.append(f"Introduced on {self.introduction_date.strftime('%d %b %Y')}")
        if self.referred_to_committee_date:
            summary.append(f"Referred to committee on {self.referred_to_committee_date.strftime('%d %b %Y')}")
        if self.passed_in_ls_date:
            summary.append(f"Passed Lok Sabha on {self.passed_in_ls_date.strftime('%d %b %Y')}")
        if self.passed_in_rs_date:
            summary.append(f"Passed Rajya Sabha on {self.passed_in_rs_date.strftime('%d %b %Y')}")
        if self.assent_date:
            summary.append(f"Received Presidential Assent on {self.assent_date.strftime('%d %b %Y')}")
        if self.act_number:
            summary.append(f"Act No. {self.act_number}")
        return " → ".join(summary) if summary else "Bill under consideration"
    
    @property
    def bill_display_name(self):
        """Generate display name for the bill"""
        if self.bill_number_display:
            return self.bill_number_display
        elif self.bill_number:
            return f"Bill No. {self.bill_number}"
        return "Bill"


class BillUpdate(models.Model):
    """Track updates to bills"""
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='updates')
    update_date = models.DateTimeField(default=timezone.now)
    update_type = models.CharField(max_length=50)
    description = models.TextField()
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-update_date']


class ScrapeSource(models.Model):
    """Track different data sources"""
    SOURCE_TYPES = [
        ('PRS', 'PRS India'),
        ('LOK_SABHA', 'Lok Sabha'),
        ('RAJYA_SABHA', 'Rajya Sabha'),
        ('DATA_GOV_IN', 'data.gov.in'),
        ('MPA', 'Ministry of Parliamentary Affairs'),
        ('SANSAD', 'Sansad Website'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    base_url = models.URLField(max_length=500)
    is_active = models.BooleanField(default=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    scrape_frequency = models.IntegerField(default=24)
    
    def __str__(self):
        return f"{self.name} ({self.source_type})" 


class State(models.Model):
    """Indian States"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.name


class Party(models.Model):
    """Political Parties"""
    name = models.CharField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.name} ({self.abbreviation})" if self.abbreviation else self.name


class MP(models.Model):
    """Member of Parliament"""
    HOUSE_CHOICES = [
        ('LOK_SABHA', 'Lok Sabha'),
        ('RAJYA_SABHA', 'Rajya Sabha'),
    ]
    name = models.CharField(max_length=200)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='mps')
    constituency = models.CharField(max_length=200)
    house = models.CharField(max_length=20, choices=HOUSE_CHOICES)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='mps')

    def __str__(self):
        return f"{self.name} ({self.get_house_display()} - {self.constituency})"


class MLA(models.Model):
    """Member of Legislative Assembly"""
    name = models.CharField(max_length=200)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='mlas')
    constituency = models.CharField(max_length=200)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='mlas')

    def __str__(self):
        return f"{self.name} ({self.constituency})"
# tracker/models.py - Add this new model

class StateBill(models.Model):
    """Model for State Legislative Assembly Bills"""
    
    BILL_STATUS = [
        ('PENDING', 'Pending'),
        ('PASSED', 'Passed'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
        ('AWAITING_ASSENT', 'Awaiting Governor/President Assent'),
        ('ENACTED', 'Enacted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill_id = models.CharField(max_length=50, unique=True)
    bill_number = models.CharField(max_length=50, blank=True)
    title = models.CharField(max_length=500)
    state = models.CharField(max_length=100)  # State name
    legislative_assembly = models.CharField(max_length=200)  # e.g., 'Karnataka Legislative Assembly'
    introduction_date = models.DateField(null=True, blank=True)
    passed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=BILL_STATUS, default='PENDING')
    key_features = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    introduced_by = models.CharField(max_length=200, blank=True)
    ministry = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-introduction_date']
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['status']),
            models.Index(fields=['introduction_date']),
        ]
    
    def __str__(self):
        return f"{self.state}: {self.title[:50]}"