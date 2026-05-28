# ============================================================
# appointments/utils.py — Translation helpers
# ============================================================

from deep_translator import GoogleTranslator


def translate_to_english(text):
    """
    Translate text to English if it's not already English.
    Returns (translated_text, detected_language_code).
    """
    try:
        translator = GoogleTranslator(source='auto', target='en')
        result = translator.translate(text)
        # Try to detect language
        try:
            from deep_translator import single_detection
            lang = single_detection(text, api_key='')
        except Exception:
            lang = 'en'
        return result or text, lang
    except Exception:
        return text, 'en'


def language_display_name(lang_code):
    """Map common language codes to display names."""
    names = {
        'en': 'English',
        'tl': 'Tagalog / Filipino',
        'fil': 'Filipino',
        'ceb': 'Cebuano',
        'es': 'Spanish',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese',
    }
    return names.get(lang_code, lang_code)
