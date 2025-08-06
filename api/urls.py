"""
API URLs for OralHealth app.
"""

from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # API Documentation
    path('', views.APIDocsView.as_view(), name='docs'),
    
    # API Endpoints
    path('recommendations/', views.recommendations_api, name='recommendations'),
    path('guidelines/', views.guidelines_api, name='guidelines'),
    path('cochrane/', views.cochrane_reviews_api, name='cochrane'),
    path('stats/', views.stats_api, name='stats'),
    path('metadata/', views.metadata_api, name='metadata'),
]