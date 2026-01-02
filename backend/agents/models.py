from django.db import models

class Company(models.Model):
    """
    The 'Golden Record'. 
    This table stores the CLEAN, VALIDATED data after Agent 2 processes the raw findings.
    """
    # Core Identity
    name = models.CharField(max_length=255, unique=True)
    cin = models.CharField(max_length=21, unique=True, blank=True, null=True) # Unique ID for Indian Cos
    domain = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)

    # Legal / ROC Data (Govt Verified)
    incorporation_date = models.DateField(blank=True, null=True)
    legal_status = models.CharField(max_length=50, blank=True)  # e.g., "Active", "Strike Off"

    # Market Intelligence (Financials & Size)
    estimated_revenue = models.CharField(max_length=100, blank=True)
    employee_count = models.IntegerField(blank=True, null=True)
    
    # Technographics (Stored as JSON)
    tech_stack = models.JSONField(default=list, blank=True) 
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class CompanyRawData(models.Model):
    """
    The 'Evidence Locker'.
    Agent 1 dumps raw text here from Zauba, Tofler, LinkedIn, etc.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='raw_data')
    
    # What was the user asking for? (e.g., "Find director email")
    user_prompt = models.TextField(default="General Info") 
    
    # Where did we find it?
    source_domain = models.CharField(max_length=100) # e.g. "zaubacorp.com"
    source_url = models.URLField(max_length=500)
    
    # Extracted metadata (Optional, just to help searching)
    found_cin = models.CharField(max_length=50, null=True, blank=True)
    
    # The actual messy text snippet
    raw_text = models.TextField() 
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.name} - {self.source_domain}"