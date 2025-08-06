"""
URL configuration for guidelines app.
"""

from django.urls import path
from . import views

app_name = 'guidelines'

urlpatterns = [
    path('', views.home_view, name='home'),
    
    # Recommendations
    path('recommendations/', views.RecommendationListView.as_view(), name='recommendation_list'),
    path('recommendations/<int:pk>/', views.RecommendationDetailView.as_view(), name='recommendation_detail'),
    
    # Guidelines
    path('guidelines/', views.GuidelineListView.as_view(), name='guideline_list'),
    path('guidelines/<int:pk>/', views.GuidelineDetailView.as_view(), name='guideline_detail'),
    
    # Topics
    path('topics/', views.TopicListView.as_view(), name='topic_list'),
    path('topics/<slug:slug>/', views.TopicDetailView.as_view(), name='topic_detail'),
    
    # API endpoints
    path('api/search/', views.search_api, name='search_api'),
    path('api/translate/', views.translate_api, name='translate_api'),
]