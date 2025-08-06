"""
Translation functionality for OralHealth application.
Supports Google Translate API with LibreTranslate fallback.
"""

import requests
import json
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext as _
import logging

logger = logging.getLogger(__name__)


class TranslationService:
    """Translation service with multiple providers."""
    
    # Supported languages for oral health content
    SUPPORTED_LANGUAGES = {
        'en': {'name': 'English', 'flag': '🇬🇧'},
        'es': {'name': 'Español', 'flag': '🇪🇸'},
        'fr': {'name': 'Français', 'flag': '🇫🇷'},
        'de': {'name': 'Deutsch', 'flag': '🇩🇪'},
        'it': {'name': 'Italiano', 'flag': '🇮🇹'},
        'pt': {'name': 'Português', 'flag': '🇵🇹'},
        'ru': {'name': 'Русский', 'flag': '🇷🇺'},
        'zh': {'name': '中文', 'flag': '🇨🇳'},
        'ja': {'name': '日本語', 'flag': '🇯🇵'},
        'ko': {'name': '한국어', 'flag': '🇰🇷'},
        'ar': {'name': 'العربية', 'flag': '🇸🇦'},
        'hi': {'name': 'हिन्दी', 'flag': '🇮🇳'},
        'tr': {'name': 'Türkçe', 'flag': '🇹🇷'},
        'nl': {'name': 'Nederlands', 'flag': '🇳🇱'},
        'sv': {'name': 'Svenska', 'flag': '🇸🇪'},
        'da': {'name': 'Dansk', 'flag': '🇩🇰'},
        'no': {'name': 'Norsk', 'flag': '🇳🇴'},
        'fi': {'name': 'Suomi', 'flag': '🇫🇮'},
        'pl': {'name': 'Polski', 'flag': '🇵🇱'},
        'cs': {'name': 'Čeština', 'flag': '🇨🇿'},
        'hu': {'name': 'Magyar', 'flag': '🇭🇺'},
        'ro': {'name': 'Română', 'flag': '🇷🇴'},
        'el': {'name': 'Ελληνικά', 'flag': '🇬🇷'},
        'he': {'name': 'עברית', 'flag': '🇮🇱'},
        'th': {'name': 'ไทย', 'flag': '🇹🇭'},
        'vi': {'name': 'Tiếng Việt', 'flag': '🇻🇳'},
        'id': {'name': 'Bahasa Indonesia', 'flag': '🇮🇩'},
        'ms': {'name': 'Bahasa Melayu', 'flag': '🇲🇾'},
        'uk': {'name': 'Українська', 'flag': '🇺🇦'},
        'bg': {'name': 'Български', 'flag': '🇧🇬'},
        'hr': {'name': 'Hrvatski', 'flag': '🇭🇷'},
        'sk': {'name': 'Slovenčina', 'flag': '🇸🇰'},
        'sl': {'name': 'Slovenščina', 'flag': '🇸🇮'},
        'lt': {'name': 'Lietuvių', 'flag': '🇱🇹'},
        'lv': {'name': 'Latviešu', 'flag': '🇱🇻'},
        'et': {'name': 'Eesti', 'flag': '🇪🇪'},
    }
    
    def __init__(self):
        self.google_api_key = getattr(settings, 'GOOGLE_TRANSLATE_API_KEY', None)
        self.libretranslate_url = getattr(settings, 'LIBRETRANSLATE_URL', 'https://libretranslate.de')
        
    def get_cache_key(self, text, target_lang, source_lang='en'):
        """Generate cache key for translation."""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:16]
        return f"translation:{source_lang}:{target_lang}:{text_hash}"
    
    def translate_with_google(self, text, target_lang, source_lang='en'):
        """Translate using Google Translate API."""
        if not self.google_api_key:
            return None
            
        try:
            url = f"https://translation.googleapis.com/language/translate/v2"
            params = {
                'key': self.google_api_key,
                'q': text,
                'target': target_lang,
                'source': source_lang,
                'format': 'text'
            }
            
            response = requests.post(url, data=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if 'data' in result and 'translations' in result['data']:
                return result['data']['translations'][0]['translatedText']
                
        except Exception as e:
            logger.error(f"Google Translate error: {e}")
            
        return None
    
    def translate_with_libretranslate(self, text, target_lang, source_lang='en'):
        """Translate using LibreTranslate (free)."""
        try:
            url = f"{self.libretranslate_url}/translate"
            data = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text'
            }
            
            response = requests.post(url, data=data, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            if 'translatedText' in result:
                return result['translatedText']
                
        except Exception as e:
            logger.error(f"LibreTranslate error: {e}")
            
        return None
    
    def translate_text(self, text, target_lang, source_lang='en'):
        """
        Translate text with caching and fallback providers.
        """
        if not text or not text.strip():
            return text
            
        if target_lang == source_lang:
            return text
            
        if target_lang not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language: {target_lang}")
            return text
        
        # Check cache first
        cache_key = self.get_cache_key(text, target_lang, source_lang)
        cached_translation = cache.get(cache_key)
        if cached_translation:
            return cached_translation
        
        # Try Google Translate first
        translation = self.translate_with_google(text, target_lang, source_lang)
        
        # Fallback to LibreTranslate
        if not translation:
            translation = self.translate_with_libretranslate(text, target_lang, source_lang)
        
        # If all fails, return original text
        if not translation:
            logger.warning(f"Translation failed for {source_lang} -> {target_lang}")
            return text
        
        # Cache the result for 7 days
        cache.set(cache_key, translation, 60 * 60 * 24 * 7)
        
        return translation
    
    def translate_recommendation(self, recommendation, target_lang):
        """
        Translate a recommendation object.
        Returns a dictionary with translated fields.
        """
        if target_lang == 'en':
            return {
                'title': recommendation.title,
                'text': recommendation.text,
                'target_population': recommendation.target_population,
                'clinical_context': recommendation.clinical_context,
            }
        
        return {
            'title': self.translate_text(recommendation.title, target_lang),
            'text': self.translate_text(recommendation.text, target_lang),
            'target_population': self.translate_text(recommendation.target_population, target_lang) if recommendation.target_population else '',
            'clinical_context': self.translate_text(recommendation.clinical_context, target_lang) if recommendation.clinical_context else '',
        }
    
    def translate_topic(self, topic, target_lang):
        """Translate a topic object."""
        if target_lang == 'en':
            return {
                'name': topic.name,
                'description': topic.description,
            }
        
        return {
            'name': self.translate_text(topic.name, target_lang),
            'description': self.translate_text(topic.description, target_lang) if topic.description else '',
        }
    
    @classmethod
    def get_supported_languages(cls):
        """Get list of supported languages."""
        return cls.SUPPORTED_LANGUAGES


# Global instance
translator = TranslationService()