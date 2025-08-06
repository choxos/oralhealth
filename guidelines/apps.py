"""
App configuration for guidelines.
"""

from django.apps import AppConfig


class GuidelinesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'guidelines'
    verbose_name = 'Oral Health Guidelines'