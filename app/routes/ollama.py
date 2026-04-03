"""
Ollama AI Routes - Generate and View AI Expert Responses
Integrated directly into Flask app (no separate server needed)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from bson.objectid import ObjectId
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

from .. import mongo
from ..routes.auth import login_required
from ..services.ollama_service import generate_all_responses

bp = Blueprint('ollama', __name__, url_prefix='/ollama')


@bp.route('/answers')
@login_required
def answers():
    """View AI answers for user's latest prediction"""
    user_id = ObjectId(session['user_id'])
    user = mongo.db.users.find_one({'_id': user_id})

    # Get latest prediction for THIS user (use find with sort and limit)
    prediction = mongo.db.predictions.find(
        {'user_id': user_id}
    ).sort('timestamp', -1).limit(1).next() if mongo.db.predictions.count_documents({'user_id': user_id}) > 0 else None

    if prediction:
        prediction['_id'] = str(prediction['_id'])
        prediction['user_id'] = str(prediction['user_id'])
        if 'image_data' in prediction:
            # Convert binary to base64 for display
            prediction['image_base64'] = base64.b64encode(prediction['image_data']).decode('utf-8')
    else:
        prediction = None

    return render_template('ollama/answers.html', user=user, prediction=prediction)


@bp.route('/api/generate', methods=['POST'])
@login_required
def generate_responses():
    """
    Generate Ollama AI responses for user's latest prediction.
    Responses are stored in MongoDB linked to user's prediction.
    Responses are generated in user's preferred language.
    """
    try:
        # Get user's latest prediction (use find with sort and limit)
        user_id = ObjectId(session['user_id'])
        prediction = mongo.db.predictions.find(
            {'user_id': user_id}
        ).sort('timestamp', -1).limit(1).next() if mongo.db.predictions.count_documents({'user_id': user_id}) > 0 else None

        if not prediction:
            return jsonify({'success': False, 'error': 'No prediction found'}), 404

        disease = prediction['disease']
        
        # Get user's preferred language
        user_lang = session.get('preferred_language', 'en')
        print(f"Generating Ollama responses for: {disease} in language: {user_lang}")

        # Generate responses in user's language (this takes time - 4 prompts)
        responses = generate_all_responses(disease, user_lang)

        # Update prediction in MongoDB with responses
        mongo.db.predictions.update_one(
            {'_id': prediction['_id']},
            {
                '$set': {
                    'processed': True,
                    'ollama_responses': responses,
                    'ollama_processed_at': datetime.utcnow(),
                    'language': user_lang
                }
            }
        )

        return jsonify({
            'success': True,
            'message': 'AI responses generated successfully',
            'responses': responses,
            'prediction_id': str(prediction['_id']),
            'language': user_lang
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/status')
@login_required
def check_status():
    """Check if Ollama is available"""
    try:
        import requests
        from ..config import OLLAMA_API_URL

        # Extract base URL from OLLAMA_API_URL
        ollama_base = OLLAMA_API_URL.replace('/api/generate', '')

        # Just check if the server is reachable
        response = requests.get(ollama_base, timeout=5)

        # Any response (even 404) means server is running
        return jsonify({
            'success': True,
            'status': f'Ollama server reachable at {ollama_base}',
            'response_code': response.status_code
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Cannot connect to Ollama. Ensure it is running on port 57948.'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ollama status check failed: {str(e)}'
        }), 500


@bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """
    Chat with Ollama AI assistant about crop diagnosis.
    Returns pre-generated summary on first call, then handles conversation.
    Responses are translated to user's preferred language.
    """
    try:
        data = request.json
        user_message = data.get('message', '')
        disease = data.get('disease', 'Unknown disease')
        confidence = data.get('confidence', 0)
        conversation_history = data.get('history', [])  # Get conversation history

        if not user_message:
            return jsonify({'success': False, 'error': 'No message provided'}), 400

        import requests
        from ..config import OLLAMA_API_URL, OLLAMA_MODEL
        from ..services.translation_service import translate_ollama_response

        # Get user's preferred language
        user_lang = session.get('preferred_language', 'en')

        # Get user's latest prediction to check for pre-generated responses
        user_id = ObjectId(session['user_id'])

        # Wait up to 30 seconds for Ollama processing to complete
        import time
        max_wait = 30  # seconds
        wait_interval = 1  # check every second
        waited = 0

        while waited < max_wait:
            prediction = mongo.db.predictions.find(
                {'user_id': user_id}
            ).sort('timestamp', -1).limit(1).next() if mongo.db.predictions.count_documents({'user_id': user_id}) > 0 else None

            if prediction and prediction.get('processed'):
                break  # Processing complete

            time.sleep(wait_interval)
            waited += wait_interval

        if prediction:
            prediction['_id'] = str(prediction['_id'])
            prediction['user_id'] = str(prediction['user_id'])

        # If this is the first message and we have pre-generated summary, return it
        if prediction and len(conversation_history) == 0:
            ollama_summary = prediction.get('ollama_summary')
            ollama_responses = prediction.get('ollama_responses', [])

            # If we have pre-generated summary, return it (already translated)
            if ollama_summary:
                return jsonify({
                    'success': True,
                    'response': ollama_summary,
                    'disease': disease,
                    'is_summary': True,
                    'model': OLLAMA_MODEL
                })

        # Build conversation context for follow-up messages
        system_instruction = f"""You are an expert agricultural AI assistant specializing in plant disease diagnosis and treatment.
You are helping a farmer whose crop has been diagnosed with: {disease} (with {confidence*100:.1f}% confidence).

Guidelines:
- Respond in concise, actionable bullet points
- Provide specific treatment recommendations with product names
- Include both chemical and organic options when available
- Mention prevention strategies
- Be encouraging and supportive
- Keep responses focused and practical
- Use simple language that farmers can understand

Disease Context: {disease}
"""

        # Build messages array for conversation history
        messages = [{'role': 'system', 'content': system_instruction}]

        # Add conversation history
        for msg in conversation_history:
            messages.append(msg)

        # Add current user message
        messages.append({'role': 'user', 'content': user_message})

        # Use chat API if available, otherwise use generate API
        chat_url = OLLAMA_API_URL.replace('/api/generate', '/api/chat')

        response = requests.post(
            chat_url,
            headers={'Content-Type': 'application/json'},
            json={
                'model': OLLAMA_MODEL,
                'messages': messages,
                'stream': False
            },
            timeout=120
        )

        if response.ok:
            result = response.json()
            ai_response = result.get('message', {}).get('content', '')

            if not ai_response:
                # Fallback to generate API
                full_prompt = f"{system_instruction}\n\nConversation history:\n"
                for msg in conversation_history[-4:]:  # Last 4 messages for context
                    role = "User" if msg['role'] == 'user' else "Assistant"
                    full_prompt += f"{role}: {msg['content']}\n"
                full_prompt += f"\nUser: {user_message}\n\nAssistant:"

                gen_response = requests.post(
                    OLLAMA_API_URL,
                    headers={'Content-Type': 'application/json'},
                    json={
                        'model': OLLAMA_MODEL,
                        'prompt': full_prompt,
                        'stream': False
                    },
                    timeout=120
                )
                if gen_response.ok:
                    ai_response = gen_response.json().get('response', '')

            # Translate the AI response to user's language if not English
            if user_lang != 'en':
                ai_response = translate_ollama_response(ai_response, user_lang)

            return jsonify({
                'success': True,
                'response': ai_response,
                'disease': disease,
                'is_summary': False,
                'model': OLLAMA_MODEL,
                'language': user_lang
            })
        else:
            error_msg = f'Ollama returned status {response.status_code}'
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500

    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'AI request timed out. Please try again.'
        }), 500
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Connection error: {str(e)}. Make sure Ollama is running.'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/translate-speech', methods=['POST'])
@login_required
def translate_speech():
    """
    Translate speech-to-text from user's language to English.
    Used for voice input in chatbot.
    """
    try:
        data = request.json
        text = data.get('text', '')
        source_lang = data.get('source_lang', 'en')
        target_lang = data.get('target_lang', 'en')

        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400

        from ..services.translation_service import translate_speech_to_text

        # Translate from user's language to English
        translated_text = translate_speech_to_text(text, source_lang, target_lang)

        return jsonify({
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/user-language')
@login_required
def get_user_language():
    """Get user's preferred language for voice input"""
    try:
        user_lang = session.get('preferred_language', 'en')

        return jsonify({
            'success': True,
            'language': user_lang
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
