"""
Context processors for OralHealth app.
Provides global context variables for all templates.
"""

from django.conf import settings
from datetime import datetime
import json


def app_context(request):
    """
    Add OralHealth-specific context variables to all templates.
    """
    from oralhealth.translation import translator
    
    return {
        'app_name': getattr(settings, 'APP_NAME', 'OralHealth'),
        'app_description': getattr(settings, 'APP_DESCRIPTION', 'Oral Health Recommendations Database'),
        'app_version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'app_domain': getattr(settings, 'APP_DOMAIN', 'oralhealth.xeradb.com'),
        'current_year': datetime.now().year,
        'supported_languages': json.dumps(translator.get_supported_languages()),
        'xera_apps': [
            {
                'name': 'OST',
                'description': 'Open Science Tracker',
                'url': 'https://ost.xeradb.com',
                'icon': 'fas fa-microscope',
            },
            {
                'name': 'PRCT',
                'description': 'Post-Retraction Citation Tracker',
                'url': 'https://prct.xeradb.com',
                'icon': 'fas fa-exclamation-triangle',
            },
            {
                'name': 'CIHRPT',
                'description': 'CIHR Projects (Canada)',
                'url': 'https://cihrpt.xeradb.com',
                'icon': 'fas fa-flag',
            },
            {
                'name': 'TTEdb',
                'description': 'Target Trial Emulation',
                'url': 'https://ttedb.xeradb.com',
                'icon': 'fas fa-flask',
            },
            {
                'name': 'OralHealth',
                'description': 'Oral Health Recommendations',
                'url': 'https://oralhealth.xeradb.com',
                'icon': 'fas fa-tooth',
                'active': True,
            },
        ]
    }