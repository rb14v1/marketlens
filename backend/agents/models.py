from django.db import models

class Company(models.Model):
    # Core Identity
    name = models.CharField(max_length=255, unique=True)
    domain = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)

    # Legal / ROC Data (Govt Verified)
    incorporation_date = models.DateField(blank=True, null=True)
    legal_status = models.CharField(max_length=50, blank=True)  # e.g., "Active"

    # Market Intelligence (Financials & Size)
    estimated_revenue = models.CharField(max_length=100, blank=True)
    employee_count = models.IntegerField(blank=True, null=True)
    
    # Technographics (Stored as JSON)
    tech_stack = models.JSONField(default=list, blank=True) 
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name