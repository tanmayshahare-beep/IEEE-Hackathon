"""
Prediction Routes - Upload, Process, View History
All predictions are traceable to users via MongoDB user_id
Predictions are translated to user's preferred language
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from bson.objectid import ObjectId
from bson.binary import Binary
from datetime import datetime
from PIL import Image
from io import BytesIO
import base64
import os

from .. import mongo
from ..routes.auth import login_required
from ..services.image_processor import get_predictor
from ..services.translation_service import (
    translate_prediction_result, get_user_language,
    translate_yield_impact_data, translate_disease_impact, translate_expected_yield,
    translate_crop_type
)

bp = Blueprint('predictions', __name__, url_prefix='/predictions')


@bp.route('/upload')
@login_required
def upload_page():
    """Disease detection upload page"""
    return render_template('predictions/upload.html')


@bp.route('/api/predict', methods=['POST'])
@login_required
def predict():
    """
    Upload image, run blur detection + CNN prediction, store in MongoDB.
    Every prediction is linked to user_id for full traceability.
    """
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No image selected'}), 400
    
    try:
        # Read image
        image_bytes = file.read()
        image = Image.open(BytesIO(image_bytes))
        
        # Save to user's folder
        user_folder = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'uploads',
            session['user_id']
        )
        os.makedirs(user_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"prediction_{timestamp}_{file.filename}"
        filepath = os.path.join(user_folder, filename)
        image.save(filepath)
        
        # Run prediction
        predictor = get_predictor()

        if predictor is None:
            disease = "Model not loaded"
            confidence = 0.0
            recommendation = "CNN model not available. Check if best_model.pth exists."
            blur_result = {'is_blurry': False, 'variance': 0.0}
            top3_predictions = []
        else:
            result = predictor.predict(filepath)

            if not result['success']:
                # Handle leaf detection failure - not a leaf
                if result.get('retake_reason') == 'not_a_leaf':
                    return jsonify({
                        'success': False,
                        'error': result.get('error', 'Image does not contain a leaf'),
                        'leaf_detection': result.get('leaf_detection', {}),
                        'needs_retake': True,
                        'retake_reason': 'not_a_leaf'
                    }), 400
                
                # Handle low confidence - ask user to retake
                if result.get('needs_retake'):
                    response_data = {
                        'success': False,
                        'error': result.get('error', 'Image not recognized'),
                        'blur_result': result.get('blur_result', {}),
                        'confidence': result.get('confidence', 0),
                        'needs_retake': True,
                        'retake_reason': result.get('retake_reason', 'unknown')
                    }
                    
                    # Include top 3 predictions for debugging (low confidence only)
                    if result.get('is_low_confidence'):
                        response_data['top3_predictions'] = result.get('top3_predictions', [])
                        response_data['detected_disease'] = result.get('disease', 'Unknown')
                    
                    return jsonify(response_data), 400

                # Handle other errors
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Prediction failed'),
                    'blur_result': result.get('blur_result', {}),
                    'needs_retake': False
                }), 500

            disease = result['disease']
            confidence = result['confidence']
            recommendation = result['recommendation']
            blur_result = result['blur_result']
            top3_predictions = result.get('top3_predictions', [])

        # Get user's preferred language
        user_lang = get_user_language()
        
        # Translate prediction result to user's language
        translated_result = translate_prediction_result(result, user_lang)
        disease_translated = translated_result['disease']
        recommendation_translated = translated_result['recommendation']

        # Store image as binary in MongoDB (traceable to user)
        image_buffer = BytesIO()
        image.save(image_buffer, format='PNG')
        image_buffer.seek(0)
        image_binary = Binary(image_buffer.read())

        # Create prediction document with user_id link (store both original and translated)
        prediction_doc = {
            'user_id': ObjectId(session['user_id']),  # ← TRACEABILITY
            'image_filename': filename,
            'image_data': image_binary,
            'disease': disease,  # Original disease name (for Ollama)
            'disease_translated': disease_translated,  # Translated disease name
            'confidence': confidence,
            'blur_variance': blur_result.get('variance', 0.0),
            'is_blurry': blur_result.get('is_blurry', False),
            'recommendation': recommendation_translated,  # Translated recommendation
            'processed': False,
            'ollama_responses': [],
            'crop_info': None,
            'yield_analysis': None,
            'language': user_lang,
            'timestamp': datetime.utcnow()
        }
        
        # Insert into predictions collection
        result = mongo.db.predictions.insert_one(prediction_doc)
        prediction_id = str(result.inserted_id)

        # Update user's prediction history
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$push': {
                'predictions': {
                    'prediction_id': prediction_id,
                    'image': filename,
                    'disease': disease,
                    'confidence': confidence,
                    'timestamp': datetime.utcnow()
                }
            }}
        )

        session['latest_prediction_id'] = prediction_id

        # Trigger Ollama AI analysis in background (non-blocking)
        # This pre-generates the 4 expert responses for the chatbot
        # For healthy plants, skip Ollama and use hardcoded healthy message
        try:
            from ..services.ollama_service import generate_all_responses, generate_formatted_summary, is_healthy_plant, get_healthy_message

            # Run Ollama generation in background (don't wait for it)
            import threading
            def generate_ollama_background():
                try:
                    print(f"Background: Processing Ollama for {disease} in language {user_lang}")

                    # Check if plant is healthy
                    if is_healthy_plant(disease):
                        # Use hardcoded healthy message - no Ollama needed
                        summary = get_healthy_message(disease, user_lang)
                        print(f"Background: Plant is healthy, using predefined message")

                        mongo.db.predictions.update_one(
                            {'_id': ObjectId(prediction_id)},
                            {
                                '$set': {
                                    'processed': True,
                                    'ollama_responses': [],  # Empty for healthy plants
                                    'ollama_summary': summary,
                                    'ollama_processed_at': datetime.utcnow(),
                                    'is_healthy_plant': True,
                                    'language': user_lang
                                }
                            }
                        )
                    else:
                        # Diseased plant - generate full Ollama responses in user's language
                        print(f"Background: Generating Ollama responses for diseased plant")
                        responses = generate_all_responses(disease, user_lang)
                        summary = generate_formatted_summary(disease, responses, user_lang)

                        mongo.db.predictions.update_one(
                            {'_id': ObjectId(prediction_id)},
                            {
                                '$set': {
                                    'processed': True,
                                    'ollama_responses': responses,
                                    'ollama_summary': summary,
                                    'ollama_processed_at': datetime.utcnow(),
                                    'is_healthy_plant': False
                                }
                            }
                        )

                    print(f"Background: Ollama processing complete for prediction {prediction_id}")
                except Exception as e:
                    print(f"Background: Ollama generation failed: {e}")

            # Start background thread (don't block the response)
            thread = threading.Thread(target=generate_ollama_background)
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"Warning: Could not start Ollama background generation: {e}")

        # Return translated prediction result
        return jsonify({
            'success': True,
            'prediction_id': prediction_id,
            'disease': disease_translated,  # Translated disease name
            'disease_original': disease,  # Keep original for reference
            'confidence': confidence,
            'recommendation': recommendation_translated,  # Translated recommendation
            'blur_result': blur_result,
            'top3_predictions': top3_predictions,
            'language': user_lang,
            'ollama_ready': False  # Will be ready shortly via background thread
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/history')
@login_required
def history():
    """View user's prediction history - all traceable to logged-in user"""
    user_id = ObjectId(session['user_id'])
    user = mongo.db.users.find_one({'_id': user_id})
    
    # Get all predictions for THIS user only (traceability)
    predictions = list(mongo.db.predictions.find(
        {'user_id': user_id}  # ← Filter by user
    ).sort('timestamp', -1).limit(50))
    
    # Convert for template
    for pred in predictions:
        pred['_id'] = str(pred['_id'])
        if 'image_data' in pred:
            pred['image_base64'] = base64.b64encode(pred['image_data']).decode('utf-8')
    
    return render_template('predictions/history.html', user=user, predictions=predictions)


@bp.route('/<prediction_id>')
@login_required
def detail(prediction_id):
    """View specific prediction detail - verifies ownership"""
    try:
        prediction = mongo.db.predictions.find_one({'_id': ObjectId(prediction_id)})
        
        if not prediction:
            flash('Prediction not found.', 'danger')
            return redirect(url_for('predictions.history'))
        
        # Verify ownership (security)
        if str(prediction['user_id']) != session['user_id']:
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('predictions.history'))
        
        prediction['_id'] = str(prediction['_id'])
        if 'image_data' in prediction:
            prediction['image_base64'] = base64.b64encode(prediction['image_data']).decode('utf-8')
        
        return render_template('predictions/detail.html', prediction=prediction)
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('predictions.history'))


@bp.route('/api/latest')
@login_required
def get_latest():
    """Get user's latest prediction"""
    try:
        user_id = ObjectId(session['user_id'])
        prediction = mongo.db.predictions.find(
            {'user_id': user_id}
        ).sort('timestamp', -1).limit(1).next() if mongo.db.predictions.count_documents({'user_id': user_id}) > 0 else None

        if not prediction:
            return jsonify({'success': True, 'prediction': None})

        prediction['_id'] = str(prediction['_id'])
        prediction['user_id'] = str(prediction['user_id'])

        return jsonify({'success': True, 'prediction': prediction})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/save-crop-info', methods=['POST'])
@login_required
def save_crop_info():
    """
    Save crop information and calculate yield impact for diseased plants.
    
    Expected JSON body:
    {
        "prediction_id": "...",
        "acres": 2.5,
        "planting_month": 6,
        "farming_type": "traditional"  // optional, default: traditional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        prediction_id = data.get('prediction_id')
        acres = data.get('acres')
        planting_month = data.get('planting_month')
        farming_type = data.get('farming_type', 'traditional')
        
        # Validation
        if not prediction_id:
            return jsonify({'success': False, 'error': 'Prediction ID required'}), 400
        
        if not acres or acres <= 0:
            return jsonify({'success': False, 'error': 'Valid acreage required'}), 400
        
        if not planting_month or not (1 <= planting_month <= 12):
            return jsonify({'success': False, 'error': 'Valid planting month required (1-12)'}), 400
        
        # Get prediction
        prediction = mongo.db.predictions.find_one({'_id': ObjectId(prediction_id)})
        
        if not prediction:
            return jsonify({'success': False, 'error': 'Prediction not found'}), 404
        
        # Verify ownership
        if str(prediction['user_id']) != session['user_id']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get disease and crop type
        disease = prediction.get('disease', '')
        
        # Initialize yield calculator
        from ..services.yield_calculator import get_yield_calculator
        calculator = get_yield_calculator()
        
        crop_type = calculator.get_crop_from_disease(disease)
        
        if not crop_type:
            return jsonify({
                'success': False,
                'error': f'Cannot determine crop type from disease: {disease}'
            }), 400
        
        # Calculate expected yield (healthy baseline)
        expected_yield = calculator.calculate_expected_yield(
            crop_type=crop_type,
            acres=acres,
            farming_type=farming_type
        )
        
        # Calculate disease impact
        disease_impact = calculator.calculate_disease_impact(
            crop_type=crop_type,
            acres=acres,
            planting_month=planting_month,
            disease_name=disease
        )
        
        # Get user location for context
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        location_info = None
        if user and 'location' in user:
            location = user['location']
            if location.get('type') == 'manual':
                manual_loc = location.get('manual', {})
                location_info = {
                    'state': manual_loc.get('state'),
                    'district': manual_loc.get('district')
                }
            elif location.get('type') == 'gps':
                gps = location.get('gps', {})
                location_info = {
                    'latitude': gps.get('latitude'),
                    'longitude': gps.get('longitude')
                }
        
        # Save to prediction
        crop_info_doc = {
            'acres': acres,
            'planting_month': planting_month,
            'farming_type': farming_type,
            'crop_type': crop_type,
            'location': location_info,
            'submitted_at': datetime.utcnow()
        }
        
        mongo.db.predictions.update_one(
            {'_id': ObjectId(prediction_id)},
            {
                '$set': {
                    'crop_info': crop_info_doc,
                    'yield_analysis': {
                        'expected_yield': expected_yield,
                        'disease_impact': disease_impact,
                        'calculated_at': datetime.utcnow()
                    }
                }
            }
        )

        # Get user's preferred language
        user_lang = get_user_language()

        # Translate yield data before returning if not English
        if user_lang != 'en':
            crop_type_translated = translate_crop_type(crop_type, user_lang)
            expected_yield_translated = translate_expected_yield(expected_yield, user_lang)
            disease_impact_translated = translate_disease_impact(disease_impact, user_lang)

            return jsonify({
                'success': True,
                'crop_type': crop_type_translated,
                'expected_yield': expected_yield_translated,
                'disease_impact': disease_impact_translated,
                'message': 'Crop information saved and yield calculated successfully'
            })

        return jsonify({
            'success': True,
            'crop_type': crop_type,
            'expected_yield': expected_yield,
            'disease_impact': disease_impact,
            'message': 'Crop information saved and yield calculated successfully'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/crop-info/<prediction_id>')
@login_required
def get_crop_info(prediction_id):
    """Get crop info and yield analysis for a prediction"""
    try:
        prediction = mongo.db.predictions.find_one({'_id': ObjectId(prediction_id)})

        if not prediction:
            return jsonify({'success': False, 'error': 'Prediction not found'}), 404

        # Verify ownership
        if str(prediction['user_id']) != session['user_id']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        # Get user's preferred language
        user_lang = get_user_language()

        # Get crop info and yield analysis
        crop_info = prediction.get('crop_info')
        yield_analysis = prediction.get('yield_analysis')

        # Translate yield analysis data if available
        if yield_analysis and user_lang != 'en':
            yield_analysis = translate_yield_impact_data(yield_analysis, user_lang)
            # Also translate disease_impact and expected_yield nested data
            if 'disease_impact' in yield_analysis:
                yield_analysis['disease_impact'] = translate_disease_impact(yield_analysis['disease_impact'], user_lang)
            if 'expected_yield' in yield_analysis:
                yield_analysis['expected_yield'] = translate_expected_yield(yield_analysis['expected_yield'], user_lang)

        return jsonify({
            'success': True,
            'crop_info': crop_info,
            'yield_analysis': yield_analysis
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
