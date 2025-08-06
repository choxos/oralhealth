"""
URL configuration for cochrane app.
"""

from django.urls import path
from . import views

app_name = 'cochrane'

urlpatterns = [
    path('', views.cochrane_review_list, name='cochrane_review_list'),
    path('<str:review_id>/', views.cochrane_review_detail, name='cochrane_review_detail'),
]