"""
Ollama AI Service

Handles communication with Ollama for generating expert responses.
"""

import requests
import json
from typing import List, Dict
from datetime import datetime

from ..config import OLLAMA_API_URL, OLLAMA_MODEL, OLLAMA_PROMPTS
from .translation_service import translate_ollama_response, get_user_language


def call_ollama(prompt: str, disease: str, lang: str = 'en') -> str:
    """
    Call Ollama API to generate response for a prompt.
    Then translate the response using Google Translate.

    Args:
        prompt: Question to ask
        disease: Plant disease context
        lang: Language code (en, hi, kn)

    Returns:
        Ollama's response text (translated if not English)
    """
    try:
        # System instruction for concise, pointwise output
        system_instruction = """Respond in concise bullet points or numbered steps only.
No introductions, no conclusions, no paragraphs.
Use short, actionable statements. Include specific details (product names, values, conditions).
Format example:
• Symptom 1
• Symptom 2
• Symptom 3"""

        full_prompt = f"{system_instruction}\n\nTask: {prompt}\nDisease: {disease}"

        print(f"  → Calling Ollama at: {OLLAMA_API_URL}")
        print(f"  → Model: {OLLAMA_MODEL}")
        print(f"  → Language: {lang} (will translate after)")
        print(f"  → Prompt: {full_prompt[:150]}...")

        response = requests.post(
            OLLAMA_API_URL,
            headers={'Content-Type': 'application/json'},
            json={
                'model': OLLAMA_MODEL,
                'prompt': full_prompt,
                'stream': False
            },
            timeout=120
        )

        print(f"  → Response status: {response.status_code}")

        if response.ok:
            data = response.json()
            result = data.get('response', 'No response generated')
            print(f"  → Response received: {len(result)} characters")
            
            # Translate using Google Translate if not English
            if lang != 'en':
                print(f"  → Translating to {lang} using Google Translate...")
                from .translation_service import translate_ollama_response
                result = translate_ollama_response(result, lang)
                print(f"  → Translated: {len(result)} characters")

            return result
        else:
            error_msg = f'Error: Ollama returned status {response.status_code}'
            try:
                error_data = response.json()
                error_msg += f" - {error_data.get('error', 'Unknown error')}"
            except:
                error_msg += f" - {response.text[:200]}"
            print(f"  → {error_msg}")
            return error_msg

    except requests.exceptions.Timeout:
        error_msg = f'Error: Ollama request timed out (120s). The model may be loading or the server is slow.'
        print(f"  → {error_msg}")
        return error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f'Error calling Ollama: {str(e)}. Ensure Ollama is running with: ollama serve'
        print(f"  → {error_msg}")
        return error_msg


def generate_all_responses(disease: str, lang: str = 'en') -> List[Dict]:
    """
    Generate responses for all hardcoded prompts.

    Args:
        disease: Plant disease name
        lang: Language code (en, hi, kn)

    Returns:
        List of prompt-response pairs
    """
    responses = []

    for prompt in OLLAMA_PROMPTS:
        print(f"  Asking: {prompt}")
        response = call_ollama(prompt, disease, lang)
        responses.append({
            'prompt': prompt,
            'response': response,
            'generated_at': datetime.utcnow(),
            'language': lang
        })

    return responses


def generate_formatted_summary(disease: str, responses: List[Dict], lang: str = 'en') -> str:
    """
    Generate a formatted summary of all Ollama responses for chatbot display.

    Args:
        disease: Disease name
        responses: List of prompt-response pairs
        lang: Language code (en, hi, kn)

    Returns:
        Formatted markdown-style summary
    """
    from .translation_service import translate_disease
    
    disease_display = translate_disease(disease, lang)
    
    if lang == 'hi':
        footer = "*मैंने आपकी फसल का विश्लेषण किया है। लक्षणों, उपचार या रोकथाम के बारे में मुझसे कुछ भी पूछें!* 🌱"
    elif lang == 'kn':
        footer = "*ನಾನು ನಿಮ್ಮ ಬೆಳೆಯನ್ನು ವಿಶ್ಲೇಷಿಸಿದ್ದೇನೆ. ಲಕ್ಷಣಗಳು, ಚಿಕಿತ್ಸೆ ಅಥವಾ ತಡೆಗಟ್ಟುವಿಕೆಯ ಬಗ್ಗೆ ಏನನ್ನಾದರೂ ಕೇಳಿ!* 🌱"
    else:
        footer = "*I've analyzed your crop. Ask me anything specific about symptoms, treatment, or prevention!* 🌱"
    
    summary = f"🌿 **Expert Analysis for {disease_display}**\n\n"
    summary_titles = {
        'What are the symptoms of this plant disease?': '🔍 Symptoms',
        'What is the recommended treatment for this disease?': '💊 Treatment',
        'How can this disease be prevented in crops?': '🛡️ Prevention',
        'What are the environmental conditions that favor this disease?': '🌡️ Conditions'
    }

    for resp in responses:
        prompt = resp['prompt']
        response = resp['response']
        title = summary_titles.get(prompt, '📌 Info')
        response = response.strip()
        summary += f"**{title}:**\n{response}\n\n"

    summary += f"---\n{footer}"
    return summary


def is_healthy_plant(disease: str) -> bool:
    """
    Check if the detected disease indicates a healthy plant.
    """
    healthy_keywords = ['healthy', 'health', 'no disease', 'normal']
    disease_lower = disease.lower()
    for keyword in healthy_keywords:
        if keyword in disease_lower:
            return True
    return False


def get_healthy_message(disease: str, lang: str = 'en') -> str:
    """
    Generate a message for healthy plants in the specified language.
    """
    from .translation_service import translate_crop_type
    
    plant_name_raw = disease.split('___')[0] if '___' in disease else 'Your plant'
    plant_name = translate_crop_type(plant_name_raw, lang)

    if lang == 'hi':
        return f"""🌿 **अच्छी खबर! आपका {plant_name} स्वस्थ है!**

**वर्तमान स्थिति:** ✅ कोई रोग का पता नहीं चला

**पौधे के स्वास्थ्य को बनाए रखने के लिए सिफारिशें:**
• अपनी वर्तमान देखभाल की दिनचर्या जारी रखें
• पत्तियों के रंग या बनावट में बदलाव के लिए निगरानी करें
• उचित सिंचाई अनुसूची बनाए रखें
• पर्याप्त धूप सुनिश्चित करें
• पौधों के आसपास का क्षेत्र साफ रखें
• कीटों या रोगों के शुरुआती लक्षणों पर नजर रखें

---
*आपका पौधा बहुत अच्छा लग रहा है! मुझसे कुछ भी पूछें!* 🌱"""

    elif lang == 'kn':
        return f"""🌿 **ಸಿಹಿ ಸುದ್ದಿ! ನಿಮ್ಮ {plant_name} ಆರೋಗ್ಯಕರವಾಗಿದೆ!**

**ಪ್ರಸ್ತುತ ಸ್ಥಿತಿ:** ✅ ಯಾವುದೇ ರೋಗಗಳು ಪತ್ತೆಯಾಗಿಲ್ಲ

**ಸಸ್ಯದ ಆರೋಗ್ಯವನ್ನು ಕಾಪಾಡಿಕೊಳ್ಳಲು ಶಿಫಾರಸುಗಳು:**
• ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಆರೈಕೆ ದಿನಚರಿಯನ್ನು ಮುಂದುವರಿಸಿ
• ಎಲೆ ಬಣ್ಣ ಅಥವಾ ರಚನೆಯಲ್ಲಿ ಬದಲಾವಣೆಗಳಿಗಾಗಿ ಮೇಲ್ವಿಚಾರಣೆ ಮಾಡಿ
• ಸರಿಯಾದ ನೀರುಹಾಕುವ ವೇಳಾಪಟ್ಟಿಯನ್ನು ನಿರ್ವಹಿಸಿ
• ಸಾಕಷ್ಟು ಸೂರ್ಯನ ಬೆಳಕನ್ನು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ
• ಸಸ್ಯಗಳ ಸುತ್ತಲಿನ ಪ್ರದೇಶವನ್ನು ಸ್ವಚ್ಛವಾಗಿಡಿ
• ಕೀಟಗಳು ಅಥವಾ ರೋಗಗಳ ಆರಂಭಿಕ ಲಕ್ಷಣಗಳನ್ನು ಗಮನಿಸಿ

---
*ನಿಮ್ಮ ಸಸ್ಯವು ಅದ್ಭುತವಾಗಿದೆ! ಏನನ್ನಾದರೂ ಕೇಳಿ!* 🌱"""

    else:
        return f"""🌿 **Great News! Your {plant_name} is Healthy!**

**Current Status:** ✅ No diseases detected

**Recommendations for Maintaining Plant Health:**
• Continue your current care routine
• Monitor regularly for changes in leaf color or texture
• Maintain proper watering schedule
• Ensure adequate sunlight for your crop type
• Keep the area around plants clean
• Watch for early signs of pests or diseases

---
*Your plant looks great! Ask me anything!* 🌱"""


def process_prediction_with_ollama(disease: str) -> Dict:
    """
    Process a disease prediction through Ollama.
    
    Args:
        disease: Disease name from CNN prediction
    
    Returns:
        Dict with disease info and all Ollama responses
    """
    print(f"Processing disease through Ollama: {disease}")
    responses = generate_all_responses(disease)
    
    return {
        'disease': disease,
        'responses': responses,
        'processed_at': datetime.utcnow(),
        'prompt_count': len(responses)
    }
