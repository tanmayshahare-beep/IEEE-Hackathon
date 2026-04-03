"""
User Profile Routes - Location and Crop Information
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from bson.objectid import ObjectId
from datetime import datetime

from .. import mongo
from ..routes.auth import login_required

bp = Blueprint('profile', __name__, url_prefix='/profile')


@bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """
    Post-registration setup - collect location and initial crop information.
    This is shown once after registration before allowing full app access.
    """
    user_id = ObjectId(session['user_id'])
    user = mongo.db.users.find_one({'_id': user_id})
    
    # Check if already completed setup
    if user and user.get('location'):
        flash('Profile already set up.', 'info')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Get location data
        location_data = {
            'state': request.form.get('state', '').strip(),
            'district': request.form.get('district', '').strip(),
            'village': request.form.get('village', '').strip(),
            'pincode': request.form.get('pincode', '').strip(),
            'latitude': request.form.get('latitude', ''),
            'longitude': request.form.get('longitude', ''),
            'updated_at': datetime.utcnow()
        }
        
        # Get crop information
        crop_info = {
            'crop_type': request.form.get('crop_type', '').strip(),
            'area_acres': float(request.form.get('area_acres', 0)),
            'planting_date': datetime.strptime(request.form.get('planting_date'), '%Y-%m-%d'),
            'season_type': request.form.get('season_type', '').strip(),
            'orchard_type': request.form.get('orchard_type', 'traditional'),
            'updated_at': datetime.utcnow()
        }
        
        # Update user document
        mongo.db.users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'location': location_data,
                    'crop_info': crop_info,
                    'profile_completed': True
                }
            }
        )
        
        flash('Profile setup complete!', 'success')
        return redirect(url_for('predictions.upload_page'))
    
    # Get Indian states for dropdown
    indian_states = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
        'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
        'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
        'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
        'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
    ]
    
    return render_template(
        'profile/setup.html',
        states=indian_states,
        crop_types=['Tomato', 'Grape', 'Apple'],
        season_types=['Kharif', 'Rabi', 'Summer', 'Main_Crop', 'Early_Crop', 'Traditional', 'Non_Traditional']
    )


@bp.route('/update-crop', methods=['GET', 'POST'])
@login_required
def update_crop():
    """Update crop information for the user."""
    user_id = ObjectId(session['user_id'])
    user = mongo.db.users.find_one({'_id': user_id})
    
    if request.method == 'POST':
        crop_info = {
            'crop_type': request.form.get('crop_type', '').strip(),
            'area_acres': float(request.form.get('area_acres', 0)),
            'planting_date': datetime.strptime(request.form.get('planting_date'), '%Y-%m-%d'),
            'season_type': request.form.get('season_type', '').strip(),
            'orchard_type': request.form.get('orchard_type', 'traditional'),
            'updated_at': datetime.utcnow()
        }
        
        mongo.db.users.update_one(
            {'_id': user_id},
            {'$set': {'crop_info': crop_info}}
        )
        
        flash('Crop information updated!', 'success')
        return redirect(url_for('dashboard.index'))
    
    current_crop = user.get('crop_info', {}) if user else {}
    
    return render_template(
        'profile/update_crop.html',
        current_crop=current_crop,
        crop_types=['Tomato', 'Grape', 'Apple'],
        season_types=['Kharif', 'Rabi', 'Summer', 'Main_Crop', 'Early_Crop', 'Traditional', 'Non_Traditional']
    )


@bp.route('/api/info', methods=['GET'])
@login_required
def get_user_info():
    """Get user's location and crop information as JSON."""
    user_id = ObjectId(session['user_id'])
    user = mongo.db.users.find_one({'_id': user_id})
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'location': user.get('location'),
        'crop_info': user.get('crop_info'),
        'profile_completed': user.get('profile_completed', False)
    })


@bp.route('/check-completion')
@login_required
def check_completion():
    """Check if user has completed profile setup."""
    user_id = ObjectId(session['user_id'])
    user = mongo.db.users.find_one({'_id': user_id})
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    profile_completed = user.get('profile_completed', False)
    has_location = bool(user.get('location'))
    has_crop_info = bool(user.get('crop_info'))
    
    return jsonify({
        'success': True,
        'profile_completed': profile_completed,
        'has_location': has_location,
        'has_crop_info': has_crop_info,
        'setup_required': not (profile_completed and has_location and has_crop_info)
    })
