"""
Lightweight translation functionality for OralHealth application.
Optimized for speed with minimal dependencies.
"""

import asyncio
import hashlib
from typing import Dict, Optional
from django.conf import settings
from django.core.cache import cache
import logging

# Use httpx for async HTTP requests - much faster than requests
try:
    import httpx
except ImportError:
    import requests as httpx
    httpx.AsyncClient = None

logger = logging.getLogger(__name__)


class FastTranslationService:
    """Ultra-fast translation service with minimal overhead."""
    
    # Core languages only - most requested for medical content
    SUPPORTED_LANGUAGES = {
        'en': {'name': 'English', 'flag': '🇬🇧'},
        'es': {'name': 'Español', 'flag': '🇪🇸'},
        'fr': {'name': 'Français', 'flag': '🇫🇷'},
        'de': {'name': 'Deutsch', 'flag': '🇩🇪'},
        'it': {'name': 'Italiano', 'flag': '🇮🇹'},
        'pt': {'name': 'Português', 'flag': '🇵🇹'},
        'zh': {'name': '中文', 'flag': '🇨🇳'},
        'ja': {'name': '日本語', 'flag': '🇯🇵'},
        'ko': {'name': '한국어', 'flag': '🇰🇷'},
        'ar': {'name': 'العربية', 'flag': '🇸🇦'},
        'hi': {'name': 'हिन्दी', 'flag': '🇮🇳'},
        'ru': {'name': 'Русский', 'flag': '🇷🇺'},
    }
    
    def __init__(self):
        self.google_api_key = getattr(settings, 'GOOGLE_TRANSLATE_API_KEY', None)
        self.libretranslate_url = getattr(settings, 'LIBRETRANSLATE_URL', 'https://libretranslate.de')
        
        # Initialize async client if available
        if hasattr(httpx, 'AsyncClient'):
            self.client = httpx.AsyncClient(timeout=10.0)
        else:
            self.client = None
    
    def get_cache_key(self, text: str, target_lang: str, source_lang: str = 'en') -> str:
        """Generate fast cache key using hash."""
        text_hash = hashlib.blake2b(text.encode(), digest_size=8).hexdigest()
        return f"tr:{source_lang}:{target_lang}:{text_hash}"
    
    async def translate_async(self, text: str, target_lang: str, source_lang: str = 'en') -> Optional[str]:
        """Async translation with fallback."""
        if not text or target_lang == source_lang:
            return text
            
        # Check cache first
        cache_key = self.get_cache_key(text, target_lang, source_lang)
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        translation = None
        
        # Try Google Translate first (if available)
        if self.google_api_key and self.client:
            translation = await self._translate_google_async(text, target_lang, source_lang)
        
        # Fallback to LibreTranslate
        if not translation and self.client:
            translation = await self._translate_libretranslate_async(text, target_lang, source_lang)
        
        # Sync fallback if async not available
        if not translation:
            translation = self._translate_sync(text, target_lang, source_lang)
        
        # Cache result
        if translation:
            cache.set(cache_key, translation, 60 * 60 * 24 * 7)  # 7 days
            
        return translation or text
    
    async def _translate_google_async(self, text: str, target_lang: str, source_lang: str) -> Optional[str]:
        """Async Google Translate."""
        try:
            url = "https://translation.googleapis.com/language/translate/v2"
            data = {
                'key': self.google_api_key,
                'q': text,
                'target': target_lang,
                'source': source_lang,
                'format': 'text'
            }
            
            response = await self.client.post(url, data=data)
            if response.status_code == 200:
                result = response.json()
                return result['data']['translations'][0]['translatedText']
                
        except Exception as e:
            logger.warning(f"Google Translate failed: {e}")
            
        return None
    
    async def _translate_libretranslate_async(self, text: str, target_lang: str, source_lang: str) -> Optional[str]:
        """Async LibreTranslate."""
        try:
            url = f"{self.libretranslate_url}/translate"
            data = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text'
            }
            
            response = await self.client.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                return result.get('translatedText')
                
        except Exception as e:
            logger.warning(f"LibreTranslate failed: {e}")
            
        return None
    
    def _translate_sync(self, text: str, target_lang: str, source_lang: str) -> Optional[str]:
        """Synchronous fallback translation."""
        try:
            # Simple synchronous implementation
            if hasattr(httpx, 'post'):
                # Using httpx sync
                response = httpx.post(
                    f"{self.libretranslate_url}/translate",
                    json={
                        'q': text,
                        'source': source_lang,
                        'target': target_lang,
                        'format': 'text'
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json().get('translatedText')
            else:
                # Using requests fallback
                import requests
                response = requests.post(
                    f"{self.libretranslate_url}/translate",
                    json={
                        'q': text,
                        'source': source_lang,
                        'target': target_lang,
                        'format': 'text'
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json().get('translatedText')
                    
        except Exception as e:
            logger.warning(f"Sync translation failed: {e}")
            
        return None
    
    def translate_text(self, text: str, target_lang: str, source_lang: str = 'en') -> str:
        """Synchronous translation for compatibility."""
        if not text or target_lang == source_lang:
            return text
            
        # Check cache first
        cache_key = self.get_cache_key(text, target_lang, source_lang)
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Use sync translation
        translation = self._translate_sync(text, target_lang, source_lang)
        
        if translation:
            cache.set(cache_key, translation, 60 * 60 * 24 * 7)
            return translation
            
        return text
    
    @classmethod
    def get_supported_languages(cls) -> Dict:
        """Get supported languages."""
        return cls.SUPPORTED_LANGUAGES


# Global instance
translator = FastTranslationService()