"""
URL configuration for search app.
"""

from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_results, name='search_results'),
    path('api/', views.search_api, name='search_api'),
]