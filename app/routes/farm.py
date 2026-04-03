"""
Farm Boundaries Route
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from bson.objectid import ObjectId
from datetime import datetime
import geojson
import os

from .. import mongo
from ..routes.auth import login_required

bp = Blueprint('farm', __name__, url_prefix='/farm')


@bp.route('/boundaries', methods=['GET', 'POST'])
@login_required
def boundaries():
    """Manage farm boundaries"""
    user_id = ObjectId(session['user_id'])
    user = mongo.db.users.find_one({'_id': user_id})

    if request.method == 'POST':
        boundary_type = request.form.get('boundary_type', '')

        if boundary_type == 'upload_file':
            if 'boundary_file' not in request.files:
                flash('No file selected.', 'danger')
                return render_template('farm/boundaries.html', user=user)

            file = request.files['boundary_file']
            if file and file.filename.lower().endswith(('.geojson', '.json', '.kml')):
                # Save file
                user_folder = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    'uploads',
                    session['user_id']
                )
                os.makedirs(user_folder, exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"farm_{timestamp}_{file.filename}"
                filepath = os.path.join(user_folder, filename)
                file.save(filepath)

                # Parse and store
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if filename.lower().endswith('.kml'):
                        boundary_data = parse_kml(content)
                    else:
                        boundary_data = geojson.loads(content)

                    mongo.db.users.update_one(
                        {'_id': user_id},
                        {'$set': {
                            'farm_boundaries': {
                                'type': boundary_data.get('type', 'FeatureCollection'),
                                'features': boundary_data.get('features', []),
                                'filename': filename,
                                'uploaded_at': datetime.utcnow()
                            }
                        }}
                    )

                    flash('Farm boundaries saved successfully!', 'success')
                    return redirect(url_for('farm.view_farm_map'))

                except Exception as e:
                    flash(f'Error processing file: {str(e)}', 'danger')

        elif boundary_type == 'draw_map':
            # Handle drawn boundaries from map
            geojson_data = request.form.get('geojson_data', '')
            
            if not geojson_data:
                flash('No boundary data received. Please draw a polygon on the map.', 'warning')
                return render_template('farm/boundaries.html', user=user)
            
            try:
                # Parse GeoJSON
                boundary_data = geojson.loads(geojson_data)
                
                # Validate GeoJSON
                if not boundary_data.get('type') or not boundary_data.get('features'):
                    flash('Invalid GeoJSON format.', 'danger')
                    return render_template('farm/boundaries.html', user=user)
                
                # Save to database
                mongo.db.users.update_one(
                    {'_id': user_id},
                    {'$set': {
                        'farm_boundaries': {
                            'type': boundary_data.get('type', 'FeatureCollection'),
                            'features': boundary_data.get('features', []),
                            'filename': 'drawn_boundary.geojson',
                            'uploaded_at': datetime.utcnow(),
                            'method': 'drawn_on_map'
                        }
                    }}
                )
                
                flash('Farm boundaries drawn on map saved successfully!', 'success')
                return redirect(url_for('farm.view_farm_map'))
                
            except Exception as e:
                flash(f'Error saving drawn boundaries: {str(e)}', 'danger')
                return render_template('farm/boundaries.html', user=user)

        elif boundary_type == 'none':
            mongo.db.users.update_one(
                {'_id': user_id},
                {'$set': {'farm_boundaries': None}}
            )
            flash('Farm boundaries cleared.', 'info')
            return redirect(url_for('farm.view_farm_map'))

    return render_template('farm/boundaries.html', user=user)


@bp.route('/map')
@login_required
def view_farm_map():
    """View farm map with crop markers"""
    user_id = ObjectId(session['user_id'])
    user = mongo.db.users.find_one({'_id': user_id})
    
    # Get user's predictions with crop info
    predictions = list(mongo.db.predictions.find(
        {'user_id': user_id}
    ).sort('timestamp', -1).limit(100))
    
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
        # Extract boundary coordinates
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
            import random
            min_lat, max_lat = min(boundary_polygon['lats']), max(boundary_polygon['lats'])
            min_lng, max_lng = min(boundary_polygon['lngs']), max(boundary_polygon['lngs'])
            
            # Generate random point within boundary bounds
            lat = random.uniform(min_lat + 0.001, max_lat - 0.001)
            lng = random.uniform(min_lng + 0.001, max_lng - 0.001)
        elif user and 'location' in user:
            # Fallback to user location
            location = user['location']
            
            if location.get('type') == 'gps':
                gps = location.get('gps', {})
                lat = gps.get('latitude')
                lng = gps.get('longitude')
            elif location.get('type') == 'manual':
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
    
    return render_template('farm/farm_map.html', 
                         user=user, 
                         crop_markers=crop_markers, 
                         crop_stats=crop_stats,
                         farm_boundaries=farm_boundaries)


@bp.route('/api/boundaries', methods=['GET', 'DELETE'])
@login_required
def api_boundaries():
    """Get or delete user's farm boundaries"""
    user_id = ObjectId(session['user_id'])
    
    if request.method == 'DELETE':
        # Delete boundaries
        mongo.db.users.update_one(
            {'_id': user_id},
            {'$set': {'farm_boundaries': None}}
        )
        return jsonify({'success': True, 'message': 'Boundaries deleted'})
    
    # GET request
    user = mongo.db.users.find_one({'_id': user_id})
    boundaries = user.get('farm_boundaries') if user else None

    if boundaries:
        return jsonify({'success': True, 'has_boundaries': True, 'data': boundaries})
    else:
        return jsonify({'success': True, 'has_boundaries': False, 'data': None})


def get_state_coordinates(state_name):
    """Get approximate coordinates for Indian states"""
    state_coords = {
        'Maharashtra': (19.7515, 75.7139),
        'Karnataka': (15.3173, 75.7139),
        'Tamil Nadu': (11.1271, 78.6569),
        'Andhra Pradesh': (15.9129, 79.7400),
        'Telangana': (18.1124, 79.0193),
        'Himachal Pradesh': (31.8478, 77.2958),
        'Jammu & Kashmir': (33.7782, 76.5762),
        'Uttarakhand': (30.0668, 79.0193),
        'Punjab': (31.1471, 75.3412),
        'Haryana': (29.0588, 76.0856),
        'Uttar Pradesh': (26.8467, 80.9462),
        'Bihar': (25.0961, 85.3131),
        'West Bengal': (22.9868, 87.8550),
        'Orissa': (20.9517, 85.0985),
        'Madhya Pradesh': (22.9734, 78.6569),
        'Assam': (26.2006, 92.9376),
        'Gujarat': (22.2587, 71.1924),
        'Rajasthan': (27.0238, 74.2179),
        'Kerala': (10.8505, 76.2711)
    }
    return state_coords.get(state_name, (20.5937, 78.9629))  # Default to central India


def parse_kml(kml_content):
    """Basic KML to GeoJSON converter"""
    import re
    coord_pattern = r'<coordinates>([^<]+)</coordinates>'
    matches = re.findall(coord_pattern, kml_content)

    features = []
    for match in matches:
        coords = []
        for coord in match.strip().split():
            parts = coord.split(',')
            if len(parts) >= 2:
                try:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    coords.append([lon, lat])
                except ValueError:
                    continue

        if len(coords) >= 3:
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            features.append(geojson.Feature(
                geometry=geojson.Polygon([coords]),
                properties={}
            ))

    return geojson.FeatureCollection(features)
