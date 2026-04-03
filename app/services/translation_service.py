"""
Translation Service - Backend translation for dynamic content

Handles translation of:
1. Ollama AI responses (using Deep Translator)
2. CNN prediction results
3. Disease names and recommendations
4. Dynamic UI content
"""

from typing import Dict, List, Optional
from flask import session
from deep_translator import GoogleTranslator


# Deep Translator language codes
TRANSLATOR_LANG_CODES = {
    'hi': 'hi',      # Hindi
    'kn': 'kn',      # Kannada
    'en': 'en'       # English
}

# Initialize translator
translator = GoogleTranslator(source='en', target='hi')


# Disease name translations
DISEASE_TRANSLATIONS = {
    'Apple___Apple_scab': {
        'hi': 'सेब - सेब स्कैब रोग',
        'kn': 'ಸೇಬು - ಸೇಬು ಸ್ಕ್ಯಾಬ್ ರೋಗ'
    },
    'Apple___Black_rot': {
        'hi': 'सेब - ब्लैक रॉट रोग',
        'kn': 'ಸೇಬು - ಬ್ಲಾಕ್ ರಾಟ್ ರೋಗ'
    },
    'Apple___Cedar_apple_rust': {
        'hi': 'सेब - सीडार एप्पल रस्ट',
        'kn': 'ಸೇಬು - ಸೀಡಾರ್ ಆಪಲ್ ರಸ್ಟ್'
    },
    'Apple___healthy': {
        'hi': 'सेब - स्वस्थ',
        'kn': 'ಸೇಬು - ಆರೋಗ್ಯಕರ'
    },
    'Grape___Black_rot': {
        'hi': 'अंगूर - ब्लैक रॉट रोग',
        'kn': 'ದ್ರಾಕ್ಷಿ - ಬ್ಲಾಕ್ ರಾಟ್ ರೋಗ'
    },
    'Grape___Esca_(Black_Measles)': {
        'hi': 'अंगूर - एस्का (ब्लैक मीजल्स)',
        'kn': 'ದ್ರಾಕ್ಷಿ - ಎಸ್ಕಾ (ಬ್ಲಾಕ್ ಮೀಸಲ್ಸ್)'
    },
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)': {
        'hi': 'अंगूर - लीफ ब्लাইट',
        'kn': 'ದ್ರಾಕ್ಷಿ - ಎಲೆ ಬ್ಲೈಟ್'
    },
    'Grape___healthy': {
        'hi': 'अंगूर - स्वस्थ',
        'kn': 'ದ್ರಾಕ್ಷಿ - ಆರೋಗ್ಯಕರ'
    },
    'Tomato___Bacterial_spot': {
        'hi': 'टमाटर - बैक्टीरियल स्पॉट',
        'kn': 'ಟೊಮ್ಯಾಟೋ - ಬ್ಯಾಕ್ಟೀರಿಯಲ್ ಸ್ಪಾಟ್'
    },
    'Tomato___Early_blight': {
        'hi': 'टमाटर - अर्ली ब्लाइट',
        'kn': 'ಟೊಮ್ಯಾಟೋ - ಅರ್ಲಿ ಬ್ಲೈಟ್'
    },
    'Tomato___Late_blight': {
        'hi': 'टमाटर - लेट ब्लाइट',
        'kn': 'ಟೊಮ್ಯಾಟೋ - ಲೇಟ್ ಬ್ಲೈಟ್'
    },
    'Tomato___Leaf_Mold': {
        'hi': 'टमाटर - लीफ मोल्ड',
        'kn': 'ಟೊಮ್ಯಾಟೋ - ಎಲೆ ಬೂಷ್ಟು'
    },
    'Tomato___Septoria_leaf_spot': {
        'hi': 'टमाटर - सेप्टोरिया लीफ स्पॉट',
        'kn': 'ಟೊಮ್ಯಾಟೋ - ಸೆಪ್ಟೋರಿಯಾ ಎಲೆ ಕಲೆ'
    },
    'Tomato___Spider_mites Two-spotted_spider_mite': {
        'hi': 'टमाटर - स्पाइडर माइट्स',
        'kn': 'ಟೊಮ್ಯಾಟೋ - ಜಿಗಣಿ ಹುಳುಗಳು'
    },
    'Tomato___Target_Spot': {
        'hi': 'टमाटर - टारगेट स्पॉट',
        'kn': 'ಟೊಮ್ಯಾಟೋ - ಟಾರ್ಗೆಟ್ ಸ್ಪಾಟ್'
    },
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus': {
        'hi': 'टमाटर - येलो लीफ कर्ल वायरस',
        'kn': 'ಟೊಮ್ಯಾಟೋ - ಹಳದಿ ಎಲೆ ಸುರುಳಿ ವೈರಸ್'
    },
    'Tomato___Tomato_mosaic_virus': {
        'hi': 'टमाटर - मोज़ेक वायरस',
        'kn': 'ಟೊಮ್ಯಾಟೋ - ಮೊಸೈಕ್ ವೈರಸ್'
    },
    'Tomato___healthy': {
        'hi': 'टमाटर - स्वस्थ',
        'kn': 'ಟೊಮ್ಯಾಟೋ - ಆರೋಗ್ಯಕರ'
    }
}

# Recommendation translations
RECOMMENDATION_TRANSLATIONS = {
    'Apple___Apple_scab': {
        'hi': 'संक्रमित पत्तियों को हटाएं, बढ़ते मौसम के दौरान कैप्टन या माइक्लोब्यूटानिल जैसे कवकनाशकों का प्रयोग करें। अच्छा वायु संचार सुनिश्चित करें।',
        'kn': 'ಸೋಂಕಿತ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ, ಬೆಳೆಯುವ ಋತುವಿನಲ್ಲಿ ಕ್ಯಾಪ್ಟನ್ ಅಥವಾ ಮೈಕ್ಲೋಬ್ಯೂಟಾನಿಲ್ನಂತಹ ಶಿಲೀಂಧ್ರನಾಶಕಗಳನ್ನು ಬಳಸಿ. ಉತ್ತಮ ಗಾಳಿ ಸಂಚಾರವನ್ನು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.'
    },
    'Tomato___Early_blight': {
        'hi': 'क्लोरथालोनिल जैसे कवकनाशकों का प्रयोग करें। निचली पत्तियों को हटाएं। फसल चक्र का पालन करें।',
        'kn': 'ಕ್ಲೋರೋಥಲೋನಿಲ್ನಂತಹ ಶಿಲೀಂಧ್ರನಾಶಕಗಳನ್ನು ಬಳಸಿ. ಕೆಳಗಿನ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ. ವಾರ್ಷಿಕವಾಗಿ ಬೆಳೆ ತಿರುಗು ಅನುಸರಿಸಿ.'
    },
    'Tomato___Late_blight': {
        'hi': 'तुरंत कवकनाशकों का प्रयोग करें। संक्रमित पौधों को हटाएं। जहां संभव हो प्रतिरोधी किस्में उपयोग करें।',
        'kn': 'ತಕ್ಷಣವೇ ಶಿಲೀಂಧ್ರನಾಶಕಗಳನ್ನು ಬಳಸಿ. ಸೋಂಕಿತ ಸಸ್ಯಗಳನ್ನು ತೆಗೆದುಹಾಕಿ. ಲಭ್ಯವಿರುವಲ್ಲಿ ನಿರೋಧಕ ತಳಿಗಳನ್ನು ಬಳಸಿ.'
    }
}

# Crop type translations
CROP_TYPE_TRANSLATIONS = {
    'Apple': {
        'hi': 'सेब',
        'kn': 'ಸೇಬು'
    },
    'Grape': {
        'hi': 'अंगूर',
        'kn': 'ದ್ರಾಕ್ಷಿ'
    },
    'Tomato': {
        'hi': 'टमाटर',
        'kn': 'ಟೊಮ್ಯಾಟೋ'
    }
}

# Month translations
MONTH_TRANSLATIONS = {
    '1': {
        'hi': 'जनवरी',
        'kn': 'ಜನವರಿ'
    },
    '2': {
        'hi': 'फरवरी',
        'kn': 'ಫೆಬ್ರವರಿ'
    },
    '3': {
        'hi': 'मार्च',
        'kn': 'ಮಾರ್ಚ್'
    },
    '4': {
        'hi': 'अप्रैल',
        'kn': 'ಏಪ್ರಿಲ್'
    },
    '5': {
        'hi': 'मई',
        'kn': 'ಮೇ'
    },
    '6': {
        'hi': 'जून',
        'kn': 'ಜೂನ್'
    },
    '7': {
        'hi': 'जुलाई',
        'kn': 'ಜುಲೈ'
    },
    '8': {
        'hi': 'अगस्त',
        'kn': 'ಆಗಸ್ಟ್'
    },
    '9': {
        'hi': 'सितंबर',
        'kn': 'ಸೆಪ್ಟೆಂಬರ್'
    },
    '10': {
        'hi': 'अक्टूबर',
        'kn': 'ಅಕ್ಟೋಬರ್'
    },
    '11': {
        'hi': 'नवंबर',
        'kn': 'ನವೆಂಬರ್'
    },
    '12': {
        'hi': 'दिसंबर',
        'kn': 'ಡಿಸೆಂಬರ್'
    }
}


def get_user_language() -> str:
    """Get current user's preferred language from session"""
    return session.get('preferred_language', 'en')


def translate_disease(disease_name: str, lang: Optional[str] = None) -> str:
    """Translate disease name to user's language"""
    if lang is None:
        lang = get_user_language()
    
    if lang == 'en':
        return disease_name
    
    translations = DISEASE_TRANSLATIONS.get(disease_name, {})
    return translations.get(lang, disease_name)


def translate_recommendation(disease_name: str, recommendation: str, lang: Optional[str] = None) -> str:
    """Translate recommendation to user's language"""
    if lang is None:
        lang = get_user_language()
    
    if lang == 'en':
        return recommendation
    
    # Check if we have a translation
    translations = RECOMMENDATION_TRANSLATIONS.get(disease_name, {})
    translated = translations.get(lang)
    
    if translated:
        return translated
    
    # Return original if no translation available
    return recommendation


def translate_crop_type(crop_type: str, lang: Optional[str] = None) -> str:
    """Translate crop type to user's language"""
    if lang is None:
        lang = get_user_language()
    
    if lang == 'en':
        return crop_type
    
    translations = CROP_TYPE_TRANSLATIONS.get(crop_type, {})
    return translations.get(lang, crop_type)


def translate_month(month: str, lang: Optional[str] = None) -> str:
    """Translate month to user's language"""
    if lang is None:
        lang = get_user_language()
    
    if lang == 'en':
        return month
    
    translations = MONTH_TRANSLATIONS.get(str(month), {})
    return translations.get(lang, month)


def translate_prediction_result(result: Dict, lang: Optional[str] = None) -> Dict:
    """Translate a complete prediction result"""
    if lang is None:
        lang = get_user_language()
    
    if lang == 'en':
        return result
    
    translated = result.copy()
    
    # Translate disease name
    if 'disease' in translated:
        translated['disease'] = translate_disease(translated['disease'], lang)
    
    # Translate recommendation
    if 'recommendation' in translated:
        translated['recommendation'] = translate_recommendation(
            result.get('disease', ''),
            translated['recommendation'],
            lang
        )
    
    return translated


def translate_ollama_response(response_text: str, lang: str) -> str:
    """
    Translate Ollama response using Google Translate (via deep-translator).
    
    Args:
        response_text: English text from Ollama
        lang: Target language code (hi, kn)
    
    Returns:
        Translated text
    """
    if lang == 'en':
        return response_text
    
    try:
        # Get target language code - use full language codes for deep-translator
        lang_map = {
            'hi': 'hindi',
            'kn': 'kannada',
            'en': 'english'
        }
        target_lang = lang_map.get(lang, 'hindi')
        
        # Create translator for this language
        translator = GoogleTranslator(source='english', target=target_lang)
        
        # Translate using Google Translate
        translated = translator.translate(response_text)
        
        # Return translated text
        return translated
        
    except Exception as e:
        print(f"Translation error: {e}")
        # Fallback: return original with note
        if lang == 'hi':
            return f"[अनुवाद उपलब्ध नहीं है]\n\n{response_text}"
        elif lang == 'kn':
            return f"[ಅನುವಾದ ಲಭ್ಯವಿಲ್ಲ]\n\n{response_text}"
        else:
            return response_text


def translate_yield_impact_data(data: Dict, lang: Optional[str] = None) -> Dict:
    """Translate yield impact analysis data"""
    if lang is None:
        lang = get_user_language()

    if lang == 'en':
        return data

    translated = data.copy()

    # Translate crop type
    if 'crop_type' in translated:
        translated['crop_type'] = translate_crop_type(translated['crop_type'], lang)

    # Translate planting month
    if 'planting_month' in translated:
        translated['planting_month'] = translate_month(translated['planting_month'], lang)

    # Translate yield analysis nested data
    if 'yield_analysis' in translated:
        translated['yield_analysis'] = translate_yield_analysis(translated['yield_analysis'], lang)

    if 'disease_impact' in translated:
        translated['disease_impact'] = translate_disease_impact(translated['disease_impact'], lang)

    if 'expected_yield' in translated:
        translated['expected_yield'] = translate_expected_yield(translated['expected_yield'], lang)

    return translated


def translate_yield_analysis(data: Dict, lang: Optional[str] = None) -> Dict:
    """Translate yield analysis data"""
    if lang is None:
        lang = get_user_language()

    if lang == 'en' or not data:
        return data

    translated = data.copy()

    # Translate crop_type if present
    if 'crop_type' in translated:
        translated['crop_type'] = translate_crop_type(translated['crop_type'], lang)

    return translated


def translate_disease_impact(data: Dict, lang: Optional[str] = None) -> Dict:
    """Translate disease impact data with all nested fields"""
    if lang is None:
        lang = get_user_language()

    if lang == 'en' or not data:
        return data

    translated = data.copy()

    # Translate crop type
    if 'crop_type' in translated:
        translated['crop_type'] = translate_crop_type(translated['crop_type'], lang)

    # Translate planting month and add translated version
    if 'planting_month' in translated:
        translated['planting_month_translated'] = translate_month(translated['planting_month'], lang)

    # Translate yield_loss section
    if 'yield_loss' in translated:
        translated['yield_loss'] = translate_yield_loss(translated['yield_loss'], lang)

    # Translate economic_impact section
    if 'economic_impact' in translated:
        translated['economic_impact'] = translate_economic_impact(translated['economic_impact'], lang)

    return translated


def translate_yield_loss(data: Dict, lang: Optional[str] = None) -> Dict:
    """Translate yield loss data"""
    if lang is None:
        lang = get_user_language()

    if lang == 'en' or not data:
        return data

    # Just return a copy - numeric values don't need translation
    return data.copy()


def translate_economic_impact(data: Dict, lang: Optional[str] = None) -> Dict:
    """Translate economic impact data"""
    if lang is None:
        lang = get_user_language()

    if lang == 'en' or not data:
        return data

    # Just return a copy - numeric values don't need translation
    return data.copy()


def translate_expected_yield(data: Dict, lang: Optional[str] = None) -> Dict:
    """Translate expected yield data"""
    if lang is None:
        lang = get_user_language()

    if lang == 'en' or not data:
        return data

    translated = data.copy()

    # Translate crop type
    if 'crop_type' in translated:
        translated['crop_type'] = translate_crop_type(translated['crop_type'], lang)

    return translated


def translate_speech_to_text(text: str, source_lang: str, target_lang: str = 'en') -> str:
    """
    Translate speech-to-text result from user's language to English (or other target).
    Uses Google Translate via deep-translator.

    Args:
        text: Text from speech recognition (in user's language)
        source_lang: Source language code (hi, kn, en)
        target_lang: Target language code (default: en)

    Returns:
        Translated text
    """
    if source_lang == target_lang:
        return text

    try:
        # Language mapping for deep-translator
        lang_map = {
            'hi': 'hindi',
            'kn': 'kannada',
            'en': 'english'
        }

        source = lang_map.get(source_lang, 'hindi')
        target = lang_map.get(target_lang, 'english')

        translator = GoogleTranslator(source=source, target=target)
        translated = translator.translate(text)

        return translated

    except Exception as e:
        print(f"Speech-to-text translation error: {e}")
        return text  # Return original if translation fails


def translate_text_to_speech(text: str, source_lang: str = 'en', target_lang: str = 'hi') -> str:
    """
    Translate text for text-to-speech output.
    Uses Google Translate via deep-translator.

    Args:
        text: Text to translate (usually English from Ollama)
        source_lang: Source language code (default: en)
        target_lang: Target language code for TTS

    Returns:
        Translated text for TTS
    """
    if source_lang == target_lang:
        return text

    try:
        # Language mapping for deep-translator
        lang_map = {
            'hi': 'hindi',
            'kn': 'kannada',
            'en': 'english'
        }

        source = lang_map.get(source_lang, 'english')
        target = lang_map.get(target_lang, 'hindi')

        translator = GoogleTranslator(source=source, target=target)
        translated = translator.translate(text)

        return translated

    except Exception as e:
        print(f"Text-to-speech translation error: {e}")
        return text  # Return original if translation fails


def get_language_name(lang_code: str) -> str:
    """Get full language name from code"""
    names = {
        'en': 'English',
        'hi': 'Hindi',
        'kn': 'Kannada'
    }
    return names.get(lang_code, 'English')


def get_speech_recognition_language(lang_code: str) -> str:
    """
    Get the BCP-47 language code for Web Speech API.
    https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API
    """
    codes = {
        'en': 'en-US',      # English (US)
        'hi': 'hi-IN',      # Hindi (India)
        'kn': 'kn-IN'       # Kannada (India)
    }
    return codes.get(lang_code, 'en-US')
