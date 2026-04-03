"""
VillageCrop - Main Application Entry Point

Run this file to start the unified web application.
All functionality (Flask + Ollama) is integrated into a single app.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.config import MODEL_PATH

app = create_app()

if __name__ == '__main__':
    # Check if model exists
    if not MODEL_PATH.exists():
        print(f"⚠️  Warning: CNN model not found at {MODEL_PATH}")
        print("   Predictions will not work until the model is available.")
        print(f"   Expected location: {MODEL_PATH}")
        print()
    
    print("=" * 60)
    print("  🌾 AgroDoc-AI - Plant Disease Detection System")
    print("=" * 60)
    print()
    print("  Starting server...")
    print()
    print("  Access the application at:")
    print("  👉 http://localhost:5000")
    print()
    print("  Test credentials:")
    print("  Username: testuser")
    print("  Password: test123")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
