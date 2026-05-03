# tracker/models_scraping.py - Add to existing models.py
from django.db import models

class ScrapingLog(models.Model):
    """Log of scraping activities"""
    STATUS_CHOICES = [
        ('STARTED', 'Started'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]
    
    source = models.CharField(max_length=50, choices=[
        ('MPA', 'MPA'),
        ('PRS', 'PRS India'),
        ('ALL', 'All Sources'),
    ])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='STARTED')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_processed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.source} - {self.started_at}"