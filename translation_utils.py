"""
Translation utilities for multi-language support.
Detects user language and translates queries to Swedish for medical searches.
"""

from langdetect import detect, LangDetectException
from google_trans_new import google_translator
import logging

logger = logging.getLogger(__name__)


class MultiLanguageHandler:
    """Handles language detection and translation for multi-language support."""
    
    def __init__(self):
        self.translator = google_translator()
        self.swedish_language_code = "sv"
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.
        
        Args:
            text: Text to detect language from
            
        Returns:
            Language code (e.g., 'en', 'sv', 'fr')
        """
        try:
            detected_lang = detect(text)
            logger.debug(f"Detected language: {detected_lang}")
            return detected_lang
        except LangDetectException:
            logger.warning("Could not detect language, defaulting to English")
            return "en"
    
    def translate_to_swedish(self, text: str, source_language: str = None) -> str:
        """
        Translate text to Swedish for medical searches.
        
        Args:
            text: Text to translate
            source_language: Source language code (auto-detected if None)
            
        Returns:
            Swedish translation of the text
        """
        if source_language is None:
            source_language = self.detect_language(text)
        
        # If already in Swedish, return as is
        if source_language == "sv":
            logger.debug("Text is already in Swedish, no translation needed")
            return text
        
        try:
            swedish_text = self.translator.translate(text, lang_src=source_language, lang_tgt=self.swedish_language_code)
            logger.debug(f"Translated to Swedish: {swedish_text}")
            return swedish_text
        except Exception as e:
            logger.error(f"Translation error: {str(e)}, returning original text")
            return text
    
    def get_language_name(self, lang_code: str) -> str:
        """Get readable language name from language code."""
        language_names = {
            'en': 'English',
            'sv': 'Swedish',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'zh': 'Chinese',
        }
        return language_names.get(lang_code, 'Unknown')


# Global instance
_language_handler = None


def get_language_handler() -> MultiLanguageHandler:
    """Get or create the language handler instance."""
    global _language_handler
    if _language_handler is None:
        _language_handler = MultiLanguageHandler()
    return _language_handler


def translate_query_for_search(query: str) -> tuple:
    """
    Translate a user query to Swedish and return both the Swedish query and the detected language.
    
    Args:
        query: User's query in any language
        
    Returns:
        Tuple of (swedish_query, detected_language)
    """
    handler = get_language_handler()
    detected_lang = handler.detect_language(query)
    swedish_query = handler.translate_to_swedish(query, detected_lang)
    return swedish_query, detected_lang
