"""
API URL configuration for guidelines app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'recommendations', api_views.RecommendationViewSet)
router.register(r'guidelines', api_views.GuidelineViewSet)
router.register(r'topics', api_views.TopicViewSet)
router.register(r'countries', api_views.CountryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('search/', api_views.search_recommendations, name='api_search'),
    path('stats/', api_views.get_statistics, name='api_stats'),
]