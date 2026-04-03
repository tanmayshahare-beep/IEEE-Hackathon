"""
Crop Context Database
Stores crop information for yield calculations including:
- Planting seasons
- Harvesting periods
- Growth duration
- Yield per acre
- Disease impact percentages
"""

# Crop configuration for India
CROP_DATA = {
    'Tomato': {
        'planting_seasons': {
            'Kharif': {'months': ['June', 'July'], 'harvest_months': ['October', 'November']},
            'Rabi': {'months': ['November', 'December'], 'harvest_months': ['April', 'May', 'June']},
            'Summer': {'months': ['February'], 'harvest_months': ['April', 'May', 'June', 'July', 'August', 'September']}
        },
        'growth_duration_days': 90,  # 3 months from transplanting to first harvest
        'yield_per_acre_kg': {
            'healthy': 15000,  # 15 tonnes (average)
            'min': 10000,      # 10 tonnes
            'max': 20000       # 20 tonnes
        },
        'disease_impact': {
            'Early_blight': {'yield_loss_percent': 30, 'severity_range': (20, 40)},
            'Late_blight': {'yield_loss_percent': 50, 'severity_range': (40, 60)},
            'Bacterial_spot': {'yield_loss_percent': 25, 'severity_range': (15, 35)},
            'Leaf_Mold': {'yield_loss_percent': 20, 'severity_range': (10, 30)},
            'Septoria_leaf_spot': {'yield_loss_percent': 25, 'severity_range': (15, 35)},
            'Spider_mites': {'yield_loss_percent': 30, 'severity_range': (20, 40)},
            'Target_Spot': {'yield_loss_percent': 25, 'severity_range': (15, 35)},
            'Yellow_Leaf_Curl_Virus': {'yield_loss_percent': 60, 'severity_range': (50, 80)},
            'Tomato_mosaic_virus': {'yield_loss_percent': 40, 'severity_range': (30, 50)},
            'healthy': {'yield_loss_percent': 0, 'severity_range': (0, 0)}
        },
        'market_price_per_kg': {
            'favourable': 16,  # ₹16/kg average
            'distress': 4      # ₹4/kg distress price
        }
    },
    
    'Grape': {
        'planting_seasons': {
            'Main_Crop': {'months': ['September', 'October', 'November'], 'harvest_months': ['December', 'January', 'February', 'March', 'April']},
            'Early_Crop': {'months': ['July', 'August'], 'harvest_months': ['October', 'November']}
        },
        'growth_duration_days': 120,  # 4 months from pruning to harvest
        'yield_per_acre_kg': {
            'healthy': 8000,   # 8 tonnes (average for table grapes)
            'min': 5000,       # 5 tonnes
            'max': 12000       # 12 tonnes
        },
        'disease_impact': {
            'Black_rot': {'yield_loss_percent': 35, 'severity_range': (25, 45)},
            'Esca_(Black_Measles)': {'yield_loss_percent': 40, 'severity_range': (30, 50)},
            'Leaf_blight_(Isariopsis_Leaf_Spot)': {'yield_loss_percent': 25, 'severity_range': (15, 35)},
            'healthy': {'yield_loss_percent': 0, 'severity_range': (0, 0)}
        },
        'market_price_per_kg': {
            'favourable': 80,  # ₹80/kg average for table grapes
            'export': 150      # ₹150/kg export quality
        }
    },
    
    'Apple': {
        'planting_seasons': {
            'Traditional': {'months': ['December', 'January', 'February'], 'harvest_months': ['July', 'August', 'September', 'October']},
            'Non_Traditional': {'months': ['December'], 'harvest_months': ['May']}
        },
        'growth_duration_days': 150,  # 5 months from pruning to harvest
        'yield_per_acre_kg': {
            'healthy_traditional': 5000,    # 5 tonnes (traditional orchards)
            'healthy_high_density': 24000,  # 24 tonnes (high-density)
            'min': 4000,
            'max': 28000
        },
        'disease_impact': {
            'Apple_scab': {'yield_loss_percent': 35, 'severity_range': (25, 45)},
            'Black_rot': {'yield_loss_percent': 30, 'severity_range': (20, 40)},
            'Cedar_apple_rust': {'yield_loss_percent': 20, 'severity_range': (10, 30)},
            'healthy': {'yield_loss_percent': 0, 'severity_range': (0, 0)}
        },
        'market_price_per_kg': {
            'traditional': 100,    # ₹100/kg traditional
            'high_density': 140    # ₹140/kg high-density
        }
    }
}


# Disease detection to crop mapping
DISEASE_TO_CROP = {
    # Tomato diseases
    'Tomato___Bacterial_spot': 'Tomato',
    'Tomato___Early_blight': 'Tomato',
    'Tomato___Late_blight': 'Tomato',
    'Tomato___Leaf_Mold': 'Tomato',
    'Tomato___Septoria_leaf_spot': 'Tomato',
    'Tomato___Spider_mites Two-spotted_spider_mite': 'Tomato',
    'Tomato___Target_Spot': 'Tomato',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus': 'Tomato',
    'Tomato___Tomato_mosaic_virus': 'Tomato',
    'Tomato___healthy': 'Tomato',
    
    # Grape diseases
    'Grape___Black_rot': 'Grape',
    'Grape___Esca_(Black_Measles)': 'Grape',
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)': 'Grape',
    'Grape___healthy': 'Grape',
    
    # Apple diseases
    'Apple___Apple_scab': 'Apple',
    'Apple___Black_rot': 'Apple',
    'Apple___Cedar_apple_rust': 'Apple',
    'Apple___healthy': 'Apple'
}


def get_crop_from_disease(disease_name: str) -> str:
    """
    Extract crop name from disease string.
    
    Args:
        disease_name: Full disease name (e.g., 'Tomato___Early_blight')
    
    Returns:
        Crop name (e.g., 'Tomato') or None if not found
    """
    if '___' in disease_name:
        return disease_name.split('___')[0]
    return DISEASE_TO_CROP.get(disease_name)


def get_disease_impact(disease_name: str) -> dict:
    """
    Get disease impact data for yield calculation.
    
    Args:
        disease_name: Full disease name
    
    Returns:
        Dictionary with yield_loss_percent and severity_range
    """
    crop = get_crop_from_disease(disease_name)
    if not crop:
        return {'yield_loss_percent': 0, 'severity_range': (0, 0)}
    
    # Extract disease type (part after ___)
    disease_type = disease_name.split('___')[1] if '___' in disease_name else 'healthy'
    
    crop_info = CROP_DATA.get(crop, {})
    disease_impact = crop_info.get('disease_impact', {})
    
    # Try exact match first
    if disease_type in disease_impact:
        return disease_impact[disease_type]
    
    # Try partial match
    for key in disease_impact:
        if key in disease_type or disease_type in key:
            return disease_impact[key]
    
    # Default to healthy
    return disease_impact.get('healthy', {'yield_loss_percent': 0, 'severity_range': (0, 0)})


def get_growth_duration(crop_name: str) -> int:
    """Get growth duration in days for a crop."""
    return CROP_DATA.get(crop_name, {}).get('growth_duration_days', 90)


def get_yield_potential(crop_name: str, orchard_type: str = 'traditional') -> dict:
    """
    Get yield potential for a crop.
    
    Args:
        crop_name: Name of crop
        orchard_type: 'traditional' or 'high_density' (for apples)
    
    Returns:
        Dictionary with healthy, min, max yield per acre in kg
    """
    crop_info = CROP_DATA.get(crop_name, {})
    yield_data = crop_info.get('yield_per_acre_kg', {})
    
    # For apples, handle high-density vs traditional
    if crop_name == 'Apple':
        if orchard_type == 'high_density':
            return {
                'healthy': yield_data.get('healthy_high_density', 24000),
                'min': yield_data.get('min', 4000),
                'max': yield_data.get('max', 28000)
            }
    
    return {
        'healthy': yield_data.get('healthy', 15000),
        'min': yield_data.get('min', 10000),
        'max': yield_data.get('max', 20000)
    }
