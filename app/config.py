"""
AgroDoc-AI - Unified Application Configuration
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Secret key
SECRET_KEY = os.getenv('SECRET_KEY', 'agrodomc-secret-key-change-in-production')

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/agrodoc-ai')
DB_NAME = 'agrodoc-ai'

# Upload Configuration
UPLOAD_FOLDER = BASE_DIR / 'app' / 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

# CNN Model Configuration
MODEL_PATH = BASE_DIR / 'models' / 'best_model.pth'  # C:\All projects\VILLAGECROP\models\best_model.pth
BLUR_THRESHOLD = 100.0
IMAGE_SIZE = 224
CONFIDENCE_THRESHOLD = 0.60  # Minimum confidence (60%) - below this, ask user to retake photo

# Ollama Configuration
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'phi3')  # RTX 4060 optimized

# Flask-Mail Configuration (Gmail SMTP)
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))  # 587 for TLS, 465 for SSL
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')  # Your Gmail address
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # Gmail App Password (NOT regular password)
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')  # Usually same as MAIL_USERNAME
MAIL_DEBUG = os.getenv('MAIL_DEBUG', 'false').lower() == 'true'

# Ollama Prompts - Optimized for concise, pointwise responses
OLLAMA_PROMPTS = [
    "List key symptoms of this plant disease in bullet points. Be concise and specific.",
    "Provide treatment recommendations as numbered steps. Include product names and dosages if applicable.",
    "List prevention methods as bullet points. Focus on practical, actionable measures.",
    "List environmental conditions that favor this disease as bullet points. Include temperature, humidity, and seasonal factors."
]

# Class names for predictions (38 classes from PlantVillage dataset)
CLASS_NAMES = [
    'Apple___Apple_scab',
    'Apple___Black_rot',
    'Apple___Cedar_apple_rust',
    'Apple___healthy',
    'Blueberry___healthy',
    'Cherry_(including_sour)___Powdery_mildew',
    'Cherry_(including_sour)___healthy',
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
    'Corn_(maize)___Common_rust_',
    'Corn_(maize)___Northern_Leaf_Blight',
    'Corn_(maize)___healthy',
    'Grape___Black_rot',
    'Grape___Esca_(Black_Measles)',
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
    'Grape___healthy',
    'Orange___Haunglongbing_(Citrus_greening)',
    'Peach___Bacterial_spot',
    'Peach___healthy',
    'Pepper,_bell___Bacterial_spot',
    'Pepper,_bell___healthy',
    'Potato___Early_blight',
    'Potato___Late_blight',
    'Potato___healthy',
    'Raspberry___healthy',
    'Soybean___healthy',
    'Squash___Powdery_mildew',
    'Strawberry___Leaf_scorch',
    'Strawberry___healthy',
    'Tomato___Bacterial_spot',
    'Tomato___Early_blight',
    'Tomato___Late_blight',
    'Tomato___Leaf_Mold',
    'Tomato___Septoria_leaf_spot',
    'Tomato___Spider_mites Two-spotted_spider_mite',
    'Tomato___Target_Spot',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
    'Tomato___Tomato_mosaic_virus',
    'Tomato___healthy'
]

# Disease recommendations
DISEASE_RECOMMENDATIONS = {
    'Apple___Apple_scab': 'Remove infected leaves, apply fungicides like captan or myclobutanil during growing season. Ensure good air circulation.',
    'Apple___Black_rot': 'Prune out mummified fruits and cankers. Apply fungicides at pink bud stage. Remove infected plant debris.',
    'Apple___Cedar_apple_rust': 'Remove nearby cedar trees if possible. Apply fungicides preventively. Plant resistant varieties.',
    'Apple___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.',
    'Blueberry___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.',
    'Cherry_(including_sour)___Powdery_mildew': 'Apply fungicides like sulfur or potassium bicarbonate. Ensure good air circulation. Remove infected plant parts.',
    'Cherry_(including_sour)___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.',
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot': 'Use resistant hybrids. Apply fungicides at silking stage. Rotate crops and till residue.',
    'Corn_(maize)___Common_rust_': 'Use resistant hybrids. Apply fungicides if severe. Monitor fields regularly during growing season.',
    'Corn_(maize)___Northern_Leaf_Blight': 'Use resistant hybrids. Apply fungicides preventively. Rotate crops and manage crop residue.',
    'Corn_(maize)___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.',
    'Grape___Black_rot': 'Remove mummified berries. Apply fungicides during bloom. Improve air circulation through pruning.',
    'Grape___Esca_(Black_Measles)': 'Remove infected wood during pruning. Avoid pruning during wet weather. No effective chemical control available.',
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)': 'Apply fungicides preventively. Remove infected leaves. Ensure proper vine spacing.',
    'Grape___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good viticultural practices.',
    'Orange___Haunglongbing_(Citrus_greening)': 'Remove infected trees immediately. Control Asian citrus psyllid vectors. Use certified disease-free nursery stock.',
    'Peach___Bacterial_spot': 'Use copper-based bactericides. Remove infected plant material. Plant resistant varieties when available.',
    'Peach___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.',
    'Pepper,_bell___Bacterial_spot': 'Use copper-based bactericides. Remove infected plants. Use disease-free seeds and transplants.',
    'Pepper,_bell___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.',
    'Potato___Early_blight': 'Apply fungicides like chlorothalonil. Remove lower leaves. Rotate crops annually.',
    'Potato___Late_blight': 'Apply fungicides immediately. Remove infected plants. Use resistant varieties when available.',
    'Potato___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.',
    'Raspberry___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.',
    'Soybean___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.',
    'Squash___Powdery_mildew': 'Apply fungicides like sulfur or potassium bicarbonate. Ensure good air circulation. Use resistant varieties.',
    'Strawberry___Leaf_scorch': 'Remove infected leaves. Apply fungicides preventively. Ensure proper plant spacing for air circulation.',
    'Strawberry___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.',
    'Tomato___Bacterial_spot': 'Use copper-based bactericides. Remove infected plants. Use disease-free seeds and transplants.',
    'Tomato___Early_blight': 'Apply fungicides like chlorothalonil. Remove lower leaves. Rotate crops annually.',
    'Tomato___Late_blight': 'Apply fungicides immediately. Remove infected plants. Use resistant varieties when available.',
    'Tomato___Leaf_Mold': 'Improve ventilation. Reduce humidity. Apply fungicides if severe.',
    'Tomato___Septoria_leaf_spot': 'Remove infected leaves. Apply fungicides. Avoid overhead watering.',
    'Tomato___Spider_mites Two-spotted_spider_mite': 'Apply miticides or insecticidal soap. Increase humidity. Introduce beneficial predators.',
    'Tomato___Target_Spot': 'Apply fungicides preventively. Remove infected plant debris. Rotate crops.',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus': 'Control whitefly vectors. Remove infected plants. Use resistant varieties.',
    'Tomato___Tomato_mosaic_virus': 'Remove infected plants. Control aphid vectors. Disinfect tools regularly.',
    'Tomato___healthy': 'Plant appears healthy. Continue regular monitoring and maintain good cultural practices.'
}
