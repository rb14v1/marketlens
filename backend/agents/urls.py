from django.urls import path
from .views import CompanyResearchView

urlpatterns = [
    path('research/', CompanyResearchView.as_view(), name='company-research'),
]