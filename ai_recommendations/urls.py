"""
URL configuration for AI recommendations app.
"""

from django.urls import path
from . import views

app_name = 'ai_recommendations'

urlpatterns = [
    # Main recommendation flow
    path('', views.AIRecommendationFormView.as_view(), name='profile_form'),
    path('results/<uuid:session_id>/', views.AIRecommendationResultsView.as_view(), name='results'),
    
    # AJAX endpoints
    path('api/status/<uuid:session_id>/', views.ajax_session_status, name='ajax_status'),
    path('api/feedback/', views.ajax_feedback, name='ajax_feedback'),
    
    # Information pages
    path('about/', views.about_ai_recommendations, name='about'),
]