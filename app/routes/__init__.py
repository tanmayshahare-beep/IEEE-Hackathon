"""
Routes Package
"""

from .auth import bp as auth_bp
from .dashboard import bp as dashboard_bp
from .predictions import bp as predictions_bp
from .ollama import bp as ollama_bp
from .farm import bp as farm_bp

__all__ = ['auth_bp', 'dashboard_bp', 'predictions_bp', 'ollama_bp', 'farm_bp']
