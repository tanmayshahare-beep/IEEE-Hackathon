"""
Dashboard Route
"""

from flask import Blueprint, render_template, session
from bson.objectid import ObjectId
from datetime import datetime
import random

from .. import mongo
from ..routes.auth import login_required

bp = Blueprint('dashboard', __name__)


@bp.route('/dashboard')
@login_required
def index():
    """Main dashboard with farm map"""
    user_id = ObjectId(session['user_id'])
    user = mongo.db.users.find_one({'_id': user_id})

    # Get user's predictions with crop info
    predictions = list(mongo.db.predictions.find(
        {'user_id': user_id}
    ).sort('timestamp', -1).limit(50))
    
    # Process predictions to extract crop data
    crop_markers = []
    crop_stats = {
        'total_predictions': len(predictions),
        'healthy_count': 0,
        'diseased_count': 0,
        'crops': {}
    }
    
    # Get farm boundaries for random marker placement
    farm_boundaries = user.get('farm_boundaries') if user else None
    boundary_polygon = None
    
    if farm_boundaries and farm_boundaries.get('features'):
        features = farm_boundaries.get('features', [])
        if features and features[0].get('geometry', {}).get('type') == 'Polygon':
            coords = features[0]['geometry']['coordinates'][0]
            boundary_polygon = {
                'lats': [coord[1] for coord in coords],
                'lngs': [coord[0] for coord in coords]
            }
    
    for pred in predictions:
        disease = pred.get('disease', '')
        is_healthy = 'healthy' in disease.lower()
        
        # Determine crop type
        crop_type = None
        if 'apple' in disease.lower():
            crop_type = 'Apple'
        elif 'grape' in disease.lower():
            crop_type = 'Grape'
        elif 'tomato' in disease.lower():
            crop_type = 'Tomato'
        
        # Update stats
        if is_healthy:
            crop_stats['healthy_count'] += 1
        else:
            crop_stats['diseased_count'] += 1
            
        if crop_type:
            if crop_type not in crop_stats['crops']:
                crop_stats['crops'][crop_type] = {'total': 0, 'healthy': 0, 'diseased': 0}
            crop_stats['crops'][crop_type]['total'] += 1
            if is_healthy:
                crop_stats['crops'][crop_type]['healthy'] += 1
            else:
                crop_stats['crops'][crop_type]['diseased'] += 1
        
        # Place marker randomly within farm boundaries OR at user location
        lat, lng = None, None
        
        if boundary_polygon:
            # Place randomly within farm boundaries
            min_lat, max_lat = min(boundary_polygon['lats']), max(boundary_polygon['lats'])
            min_lng, max_lng = min(boundary_polygon['lngs']), max(boundary_polygon['lngs'])
            
            lat = random.uniform(min_lat + 0.001, max_lat - 0.001)
            lng = random.uniform(min_lng + 0.001, max_lng - 0.001)
        elif user and 'location' in user:
            location = user['location']
            
            if location.get('type') == 'gps':
                gps = location.get('gps', {})
                lat = gps.get('latitude')
                lng = gps.get('longitude')
            elif location.get('type') == 'manual':
                from .farm import get_state_coordinates
                manual = location.get('manual', {})
                state = manual.get('state', '')
                lat, lng = get_state_coordinates(state)
        
        if lat and lng:
            crop_markers.append({
                'lat': lat,
                'lng': lng,
                'disease': disease,
                'is_healthy': is_healthy,
                'crop_type': crop_type,
                'confidence': pred.get('confidence', 0),
                'timestamp': pred.get('timestamp', datetime.utcnow()),
                'prediction_id': str(pred['_id'])
            })
    
    # Check farm boundaries
    has_farm_boundaries = user.get('farm_boundaries') is not None

    return render_template(
        'dashboard/index.html',
        user=user,
        has_farm_boundaries=has_farm_boundaries,
        prediction_count=len(predictions),
        crop_markers=crop_markers,
        crop_stats=crop_stats,
        farm_boundaries=farm_boundaries
    )
