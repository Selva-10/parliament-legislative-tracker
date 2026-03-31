# bills/models.py
from django.db import models
from django.utils import timezone
import uuid

class Bill(models.Model):
    """Bill model with all necessary fields"""
    
    BILL_STATUS = [
        ('PENDING', 'Pending'),
        ('PASSED', 'Passed'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
        ('LAPSED', 'Lapsed'),
    ]
    
    HOUSE_CHOICES = [
        ('LOK_SABHA', 'Lok Sabha'),
        ('RAJYA_SABHA', 'Rajya Sabha'),
        ('BOTH', 'Both Houses'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill_id = models.CharField(max_length=50, unique=True, help_text="Unique bill identifier")
    bill_number = models.CharField(max_length=50, blank=True, null=True)
    title = models.CharField(max_length=500)
    short_title = models.CharField(max_length=200, blank=True)
    
    # House Information
    house = models.CharField(max_length=20, choices=HOUSE_CHOICES, default='LOK_SABHA')
    introduced_in = models.CharField(max_length=50, blank=True)
    
    # Dates
    introduction_date = models.DateField(null=True, blank=True)
    passed_date = models.DateField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Status
    status = models.CharField(max_length=20, choices=BILL_STATUS, default='PENDING')
    status_details = models.TextField(blank=True)
    
    # Members Information
    introduced_by = models.CharField(max_length=500, blank=True)
    introduced_by_mp = models.CharField(max_length=200, blank=True)
    introduced_by_party = models.CharField(max_length=100, blank=True)
    
    # Ministry
    ministry = models.CharField(max_length=200, blank=True)
    
    # Description
    description = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    
    # Links
    prs_link = models.URLField(max_length=500, blank=True)
    loksabha_link = models.URLField(max_length=500, blank=True)
    rajyasabha_link = models.URLField(max_length=500, blank=True)
    pdf_link = models.URLField(max_length=500, blank=True)
    
    # Metadata
    source = models.CharField(max_length=50, default='PRS')
    source_id = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-introduction_date', 'title']
        indexes = [
            models.Index(fields=['bill_id']),
            models.Index(fields=['house']),
            models.Index(fields=['status']),
            models.Index(fields=['introduction_date']),
        ]
    
    def __str__(self):
        return f"{self.bill_id} - {self.title[:50]}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('bill_detail', args=[str(self.id)])
    
    @property
    def display_id(self):
        return self.bill_id or f"BILL-{str(self.id)[:8]}"
    
    @property
    def status_color(self):
        colors = {
            'PENDING': 'warning',
            'PASSED': 'success',
            'REJECTED': 'danger',
            'WITHDRAWN': 'secondary',
            'LAPSED': 'dark',
        }
        return colors.get(self.status, 'info')


class BillUpdate(models.Model):
    """Track updates to bills"""
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='updates')
    update_date = models.DateTimeField(default=timezone.now)
    update_type = models.CharField(max_length=50)  # STATUS_CHANGE, AMENDMENT, etc.
    description = models.TextField()
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-update_date']


class ScrapeSource(models.Model):
    """Sources for scraping bills"""
    SOURCE_TYPES = [
        ('PRS', 'PRS India'),
        ('LOK_SABHA', 'Lok Sabha'),
        ('RAJYA_SABHA', 'Rajya Sabha'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    base_url = models.URLField(max_length=500)
    is_active = models.BooleanField(default=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    scrape_frequency = models.IntegerField(default=24)  # hours
    
    def __str__(self):
        return f"{self.name} ({self.source_type})"