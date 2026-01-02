from django.contrib import admin
from .models import Company, CompanyRawData

admin.site.register(Company)
admin.site.register(CompanyRawData)