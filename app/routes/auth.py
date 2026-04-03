"""
Authentication Routes - Login, Register, OTP Verification
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from bson.objectid import ObjectId
from datetime import datetime
import os

from .. import mongo
from ..services.otp_service import otp_service

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration - Step 1: Collect user details"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Location fields
        location_type = request.form.get('location_type', 'manual')  # 'gps' or 'manual'
        gps_latitude = request.form.get('gps_latitude', '')
        gps_longitude = request.form.get('gps_longitude', '')
        state = request.form.get('state', '').strip()
        district = request.form.get('district', '').strip()

        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register.html')
        
        # Validate location
        if location_type == 'gps':
            if not gps_latitude or not gps_longitude:
                flash('GPS location is required. Please enable location access.', 'danger')
                return render_template('auth/register.html')
            try:
                lat = float(gps_latitude)
                lon = float(gps_longitude)
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    flash('Invalid GPS coordinates.', 'danger')
                    return render_template('auth/register.html')
            except ValueError:
                flash('Invalid GPS coordinates format.', 'danger')
                return render_template('auth/register.html')
        else:
            if not state or not district:
                flash('State and District are required.', 'danger')
                return render_template('auth/register.html')

        # Check if user exists
        existing_user = mongo.db.users.find_one({
            '$or': [{'username': username}, {'email': email}]
        })

        if existing_user:
            flash('Username or email already exists.', 'danger')
            return render_template('auth/register.html')

        # Store user data in session temporarily (before OTP verification)
        session['temp_user_data'] = {
            'username': username,
            'email': email,
            'password': password,
            'location_type': location_type,
            'gps_latitude': gps_latitude if location_type == 'gps' else None,
            'gps_longitude': gps_longitude if location_type == 'gps' else None,
            'state': state if location_type == 'manual' else None,
            'district': district if location_type == 'manual' else None
        }

        # Generate and send OTP
        otp = otp_service.create_otp(email)
        otp_sent = otp_service.send_otp_email(email, otp, username)

        if not otp_sent:
            flash('Failed to send verification email. Please try again.', 'danger')
            return render_template('auth/register.html')

        flash('Verification code sent to your email!', 'info')
        return redirect(url_for('auth.verify_otp'))

    return render_template('auth/register.html')


@bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """OTP verification - Step 2: Verify email with OTP"""
    # Check if user has pending registration
    temp_data = session.get('temp_user_data')
    
    if not temp_data:
        flash('Please start registration first.', 'warning')
        return redirect(url_for('auth.register'))

    email = temp_data['email']

    if request.method == 'POST':
        otp_input = request.form.get('otp', '').strip()

        if not otp_input:
            flash('Please enter the verification code.', 'danger')
            return render_template('auth/verify_otp.html', email=email)

        # Verify OTP
        is_valid = otp_service.verify_otp(email, otp_input)

        if is_valid:
            # OTP verified - create user account
            import bcrypt

            # Hash password
            hashed_password = bcrypt.hashpw(
                temp_data['password'].encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Build location object
            location_data = {
                'type': temp_data.get('location_type', 'manual')
            }
            if temp_data.get('location_type') == 'gps':
                location_data['gps'] = {
                    'latitude': float(temp_data['gps_latitude']),
                    'longitude': float(temp_data['gps_longitude'])
                }
            else:
                location_data['manual'] = {
                    'state': temp_data['state'],
                    'district': temp_data['district']
                }

            # Create user in MongoDB
            result = mongo.db.users.insert_one({
                'username': temp_data['username'],
                'email': temp_data['email'],
                'password': hashed_password,
                'email_verified': True,
                'location': location_data,  # ← NEW: Location data
                'farm_boundaries': None,
                'predictions': [],
                'created_at': datetime.utcnow()
            })

            # Create user folder
            user_folder = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'uploads',
                str(result.inserted_id)
            )
            os.makedirs(user_folder, exist_ok=True)

            # Clear temp session data
            session.pop('temp_user_data', None)

            flash('Email verified! Account created successfully. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid or expired verification code. Please try again.', 'danger')
            return render_template('auth/verify_otp.html', email=email)

    return render_template('auth/verify_otp.html', email=email)


@bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to user's email"""
    temp_data = session.get('temp_user_data')
    
    if not temp_data:
        return jsonify({'success': False, 'error': 'Registration session expired'}), 400

    email = temp_data['email']
    username = temp_data['username']

    # Resend OTP
    new_otp = otp_service.resend_otp(email)
    
    if new_otp:
        otp_sent = otp_service.send_otp_email(email, new_otp, username)
        if otp_sent:
            return jsonify({'success': True, 'message': 'Verification code resent!'})
    
    return jsonify({'success': False, 'error': 'Failed to resend. Please try again.'}), 500


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        print(f"[LOGIN ATTEMPT] Username: {username}")

        user = mongo.db.users.find_one({'username': username})
        
        print(f"[LOGIN] User found: {user is not None}")

        if user:
            # Try bcrypt first (our format), then Werkzeug
            password_hash = user['password']
            is_valid = False

            try:
                # Try bcrypt
                import bcrypt
                is_valid = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
                print(f"[LOGIN] Password valid: {is_valid}")
            except Exception as e:
                print(f"[LOGIN] Bcrypt error: {e}")
                # Fallback to Werkzeug
                from werkzeug.security import check_password_hash
                is_valid = check_password_hash(password_hash, password)
                print(f"[LOGIN] Werkzeug password valid: {is_valid}")

            if is_valid:
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                print(f"[LOGIN SUCCESS] User ID: {session['user_id']}")
                flash('Login successful!', 'success')

                # Redirect to dashboard or next URL
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard.index'))
            else:
                print(f"[LOGIN FAILED] Invalid password for {username}")
                flash('Invalid username or password.', 'danger')
        else:
            print(f"[LOGIN FAILED] User not found: {username}")
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@bp.route('/request-otp-login', methods=['POST'])
def request_otp_login():
    """Request OTP for login"""
    email = request.form.get('email', '').strip().lower()

    if not email:
        flash('Email address is required.', 'danger')
        return redirect(url_for('auth.login'))

    # Find user by email
    user = mongo.db.users.find_one({'email': email})

    if not user:
        flash('No account found with this email. Please register first.', 'danger')
        return redirect(url_for('auth.login'))

    # Generate and send OTP
    otp = otp_service.create_otp(email)
    otp_sent = otp_service.send_otp_email(email, otp, user['username'])

    if not otp_sent:
        flash('Failed to send verification code. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    # Store user ID in session for OTP verification
    session['otp_login_user_id'] = str(user['_id'])
    session['otp_login_email'] = email

    flash('Verification code sent to your email!', 'info')
    return redirect(url_for('auth.verify_otp_login'))


@bp.route('/verify-otp-login', methods=['GET', 'POST'])
def verify_otp_login():
    """Verify OTP for login"""
    # Check if user has requested OTP login
    user_id = session.get('otp_login_user_id')
    email = session.get('otp_login_email')

    if not user_id or not email:
        flash('Please request OTP code first.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        otp_input = request.form.get('otp', '').strip()

        if not otp_input:
            flash('Please enter the verification code.', 'danger')
            return render_template('auth/verify_otp_login.html', email=email)

        # Verify OTP
        is_valid = otp_service.verify_otp(email, otp_input)

        if is_valid:
            # OTP verified - log in user
            session['user_id'] = user_id
            user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            session['username'] = user['username']

            # Clear OTP session data
            session.pop('otp_login_user_id', None)
            session.pop('otp_login_email', None)

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid or expired verification code. Please try again.', 'danger')
            return render_template('auth/verify_otp_login.html', email=email)

    return render_template('auth/verify_otp_login.html', email=email)


@bp.route('/resend-otp-login', methods=['POST'])
def resend_otp_login():
    """Resend OTP for login"""
    email = session.get('otp_login_email')
    user_id = session.get('otp_login_user_id')

    if not email or not user_id:
        return jsonify({'success': False, 'error': 'Session expired. Please request OTP again.'}), 400

    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Resend OTP
    new_otp = otp_service.resend_otp(email)

    if new_otp:
        otp_sent = otp_service.send_otp_email(email, new_otp, user['username'])
        if otp_sent:
            return jsonify({'success': True, 'message': 'Verification code resent!'})

    return jsonify({'success': False, 'error': 'Failed to resend. Please try again.'}), 500


@bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/set-language/<lang>', methods=['POST'])
def set_language(lang):
    """Set user's preferred language"""
    if lang in ['en', 'hi', 'kn']:
        session['preferred_language'] = lang
        return jsonify({'success': True, 'language': lang})
    return jsonify({'success': False, 'error': 'Invalid language'}), 400


# Helper decorator
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
