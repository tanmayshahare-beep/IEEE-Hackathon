"""
VillageCrop - Unified Flask Application

Merges Flask app + Ollama integration into a single application.
All predictions are traceable to users via MongoDB.
"""

import os
from flask import Flask, session, redirect, url_for
from flask_pymongo import PyMongo
from flask_mail import Mail
from bson.objectid import ObjectId
from datetime import datetime

from .config import (
    SECRET_KEY, MONGODB_URI, UPLOAD_FOLDER, MAX_CONTENT_LENGTH,
    MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USE_SSL,
    MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, MAIL_DEBUG
)

# Initialize extensions
mongo = PyMongo()
mail = Mail()


def create_app():
    """Application factory for AgroDoc-AI"""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['MONGO_URI'] = MONGODB_URI
    app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    
    # Flask-Mail Configuration
    app.config['MAIL_SERVER'] = MAIL_SERVER
    app.config['MAIL_PORT'] = MAIL_PORT
    app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
    app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
    app.config['MAIL_USERNAME'] = MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER
    app.config['MAIL_DEBUG'] = MAIL_DEBUG

    # Initialize extensions
    mongo.init_app(app)
    mail.init_app(app)
    
    # Initialize OTP service with the app
    from .services.otp_service import otp_service
    otp_service.init_app(app)

    # Ensure upload folder exists
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    # Register blueprints
    from .routes import auth, dashboard, predictions, ollama, farm
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(predictions.bp)
    app.register_blueprint(ollama.bp)
    app.register_blueprint(farm.bp)

    # Main index route
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    # Template context processor - make functions available in templates
    @app.context_processor
    def utility_processor():
        return {
            'ObjectId': ObjectId,
            'datetime': datetime
        }

    # Add Content Security Policy headers for Leaflet.js
    @app.after_request
    def add_csp_headers(response):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self' data: blob: 'unsafe-inline' 'unsafe-eval' https: http:; "
            "script-src 'self' 'unsafe-eval' 'unsafe-inline' https: http:; "
            "style-src 'self' 'unsafe-inline' https: http:; "
            "font-src 'self' data: https: http:; "
            "img-src 'self' data: blob: https: http:; "
            "connect-src 'self' https: http: ws: wss:; "
            "frame-src 'self' https: http: blob: data:;"
        )
        return response

    return app
