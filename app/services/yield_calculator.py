"""
Yield Calculator Service

Calculates crop yield and loss based on:
- Crop type (Tomato, Grape, Apple)
- Location (State/District in India)
- Planted acres
- Planting month
- Disease detection
- Months until harvest

Based on Context_for_crops.txt data
"""

from datetime import datetime
from typing import Dict, Optional, Tuple

# Crop data from Context_for_crops.txt
CROP_DATA = {
    'Tomato': {
        'yield_per_acre': {
            'min': 10,  # tonnes
            'max': 20,  # tonnes
            'average': 15  # tonnes (150 quintals)
        },
        'investment_per_acre': {
            'min': 60000,  # INR
            'max': 125000,  # INR
            'average': 65000  # INR
        },
        'market_price_per_kg': {
            'favourable': {'min': 14, 'max': 19},  # INR
            'distress': {'min': 2, 'max': 5},  # INR
            'current': 8  # INR (conservative estimate)
        },
        'planting_seasons': {
            'Kharif': {'planting': [6, 7], 'harvest': [10, 11]},  # Jun-Jul, Oct-Nov
            'Rabi': {'planting': [11, 12], 'harvest': [4, 5, 6]},  # Nov-Dec, Apr-Jun
            'Summer': {'planting': [2], 'harvest': [4, 5, 6, 7, 8, 9]}  # Feb, Apr-Sep
        },
        'growing_states': [
            'Maharashtra', 'Bihar', 'Karnataka', 'Uttar Pradesh', 'Orissa',
            'Andhra Pradesh', 'Madhya Pradesh', 'West Bengal', 'Assam'
        ],
        'optimal_temp': {'min': 21, 'max': 27},  # °C
        # Disease spread rates (% additional yield loss per month until harvest)
        # Based on disease severity and environmental conditions
        'disease_spread_rate': {
            'early_blight': 10,  # Moderate spread - 10%/month
            'late_blight': 20,   # Rapid spread - 20%/month (can destroy crop in weeks)
            'bacterial_spot': 8,  # Moderate spread
            'leaf_mold': 6,       # Slower spread in protected conditions
            'septoria': 9,        # Moderate-fast spread
            'mosaic_virus': 12,   # Viral, spreads via vectors
            'default': 10         # Default for unknown diseases
        }
    },
    
    'Grape': {
        'yield_per_acre': {
            'min': 8,  # tonnes (varies widely)
            'max': 16,  # tonnes
            'average': 12  # tonnes
        },
        'investment_per_acre': {
            'min': 150000,  # INR (higher due to trellising, drip)
            'max': 300000,  # INR
            'average': 200000  # INR
        },
        'market_price_per_kg': {
            'table_grapes': {'min': 40, 'max': 80},  # INR
            'wine_grapes': {'min': 20, 'max': 40},  # INR
            'average': 50  # INR
        },
        'planting_seasons': {
            'Main': {'planting': [9, 10, 11], 'harvest': [12, 1, 2, 3, 4]},  # Sep-Nov, Dec-Apr
            'Early': {'planting': [7, 8], 'harvest': [10, 11]}  # Jul-Aug, Oct-Nov
        },
        'growing_states': [
            'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Andhra Pradesh',
            'Punjab', 'Haryana', 'Uttar Pradesh'
        ],
        'major_regions': {
            'Maharashtra': ['Nashik', 'Pune', 'Sangli'],
            'Karnataka': ['Bangalore', 'Mysore', 'Bagalkot'],
            'Tamil Nadu': ['Theni', 'Coimbatore'],
            'Andhra Pradesh': ['Hyderabad', 'Anantapur']
        },
        'optimal_temp': {'min': 15, 'max': 40},  # °C
        # Disease spread rates for grape diseases
        'disease_spread_rate': {
            'downy_mildew': 15,   # Fast spread in humid conditions
            'powdery_mildew': 12,  # Moderate-fast spread
            'black_rot': 14,       # Fast spread in warm, wet weather
            'esca': 3,             # Slow progression (trunk disease)
            'leaf_blight': 10,     # Moderate spread
            'default': 12          # Default for unknown diseases
        }
    },
    
    'Apple': {
        'yield_per_acre': {
            'traditional': {'min': 4, 'max': 5, 'average': 4.5},  # tonnes
            'high_density': {'min': 20, 'max': 28, 'average': 24}  # tonnes
        },
        'investment_per_acre': {
            'traditional': {'min': 100000, 'max': 200000, 'average': 150000},  # INR
            'high_density': {'min': 300000, 'max': 500000, 'average': 400000}  # INR
        },
        'market_price_per_kg': {
            'traditional': {'min': 60, 'max': 220, 'average': 140},  # INR
            'high_density': {'min': 100, 'max': 140, 'average': 120}  # INR
        },
        'planting_seasons': {
            'Traditional': {'planting': [11, 12, 1, 2], 'harvest': [7, 8, 9, 10]},  # Winter, Jul-Oct
            'Non-Traditional': {'planting': [12], 'harvest': [5]}  # Dec pruning, May harvest
        },
        'growing_states': [
            'Himachal Pradesh', 'Jammu & Kashmir', 'Uttarakhand',
            'Maharashtra', 'Karnataka', 'Telangana'
        ],
        'traditional_regions': {
            'Himachal Pradesh': ['Shimla', 'Kullu', 'Kinnaur'],
            'Jammu & Kashmir': ['Srinagar', 'Baramulla', 'Shopian'],
            'Uttarakhand': ['Nainital', 'Uttarkashi']
        },
        'optimal_temp': {'min': 15, 'max': 25},  # °C
        # Disease spread rates for apple diseases
        'disease_spread_rate': {
            'scab': 8,              # Moderate spread in wet conditions
            'black_rot': 10,        # Faster spread in warm, humid weather
            'cedar_apple_rust': 6,  # Slower (requires alternate host)
            'powdery_mildew': 7,    # Moderate spread
            'fire_blight': 15,      # Very rapid spread (bacterial)
            'default': 8            # Default for unknown diseases
        }
    }
}

# Initial disease impact (when first detected)
INITIAL_DISEASE_IMPACT = 0.12  # 12% yield loss at detection


class YieldCalculator:
    """Calculate crop yield and disease impact"""
    
    def __init__(self):
        self.crop_data = CROP_DATA
    
    def get_crop_from_disease(self, disease_name: str) -> Optional[str]:
        """Extract crop type from disease name"""
        disease_lower = disease_name.lower()

        if 'apple' in disease_lower:
            return 'Apple'
        elif 'grape' in disease_lower:
            return 'Grape'
        elif 'tomato' in disease_lower:
            return 'Tomato'

        return None

    def _get_disease_spread_rate(self, disease_name: str, spread_rates: dict) -> int:
        """
        Get disease-specific spread rate based on disease name.
        
        Args:
            disease_name: Full disease name (e.g., 'Tomato___Early_blight')
            spread_rates: Dictionary of disease-specific spread rates
            
        Returns:
            Spread rate percentage per month
        """
        disease_lower = disease_name.lower()
        
        # Check for specific diseases
        if 'late_blight' in disease_lower:
            return spread_rates.get('late_blight', spread_rates.get('default', 10))
        elif 'early_blight' in disease_lower:
            return spread_rates.get('early_blight', spread_rates.get('default', 10))
        elif 'bacterial_spot' in disease_lower:
            return spread_rates.get('bacterial_spot', spread_rates.get('default', 10))
        elif 'leaf_mold' in disease_lower:
            return spread_rates.get('leaf_mold', spread_rates.get('default', 10))
        elif 'septoria' in disease_lower:
            return spread_rates.get('septoria', spread_rates.get('default', 10))
        elif 'mosaic' in disease_lower or 'virus' in disease_lower:
            return spread_rates.get('mosaic_virus', spread_rates.get('default', 10))
        elif 'downy_mildew' in disease_lower:
            return spread_rates.get('downy_mildew', spread_rates.get('default', 12))
        elif 'powdery_mildew' in disease_lower:
            return spread_rates.get('powdery_mildew', spread_rates.get('default', 12))
        elif 'black_rot' in disease_lower:
            return spread_rates.get('black_rot', spread_rates.get('default', 12))
        elif 'esca' in disease_lower or 'measles' in disease_lower:
            return spread_rates.get('esca', spread_rates.get('default', 12))
        elif 'scab' in disease_lower:
            return spread_rates.get('scab', spread_rates.get('default', 8))
        elif 'fire_blight' in disease_lower or 'fireblight' in disease_lower:
            return spread_rates.get('fire_blight', spread_rates.get('default', 8))
        elif 'cedar' in disease_lower or 'rust' in disease_lower:
            return spread_rates.get('cedar_apple_rust', spread_rates.get('default', 8))
        
        # Default spread rate
        return spread_rates.get('default', 10)
    
    def calculate_expected_yield(self, crop_type: str, acres: float, 
                                  farming_type: str = 'traditional') -> Dict:
        """
        Calculate expected yield for a healthy crop
        
        Args:
            crop_type: 'Tomato', 'Grape', or 'Apple'
            acres: Total planted acres
            farming_type: 'traditional' or 'high_density' (for Apple)
            
        Returns:
            Dict with yield estimates and economics
        """
        if crop_type not in self.crop_data:
            return {'error': f'Unknown crop type: {crop_type}'}
        
        crop = self.crop_data[crop_type]
        yield_info = crop['yield_per_acre']
        
        # Determine yield based on farming type
        # For Apple, there are separate traditional and high_density yields
        if crop_type == 'Apple':
            if farming_type == 'high_density' and 'high_density' in yield_info:
                yield_per_acre = yield_info['high_density']
            else:
                yield_per_acre = yield_info['traditional']
        else:
            # For Tomato and Grape, use the standard yield structure
            yield_per_acre = yield_info
        
        # Calculate total yield
        min_yield = yield_per_acre['min'] * acres
        max_yield = yield_per_acre['max'] * acres
        avg_yield = yield_per_acre['average'] * acres
        
        # Calculate economics
        price_info = crop['market_price_per_kg']
        
        # For Apple, price structure is nested by farming type
        if crop_type == 'Apple':
            if farming_type == 'high_density':
                avg_price = price_info['high_density']['average']
            else:
                avg_price = price_info['traditional']['average']
        else:
            avg_price = price_info.get('current') or price_info.get('average', 10)
        
        min_revenue = min_yield * 1000 * avg_price  # Convert tonnes to kg
        max_revenue = max_yield * 1000 * avg_price
        avg_revenue = avg_yield * 1000 * avg_price

        investment_info = crop['investment_per_acre']
        # Handle Apple's nested investment structure
        if crop_type == 'Apple':
            if farming_type == 'high_density':
                total_investment = investment_info['high_density']['average'] * acres
            else:
                total_investment = investment_info['traditional']['average'] * acres
        else:
            total_investment = investment_info['average'] * acres
        
        return {
            'crop_type': crop_type,
            'acres': acres,
            'farming_type': farming_type,
            'yield': {
                'min_tonnes': round(min_yield, 2),
                'max_tonnes': round(max_yield, 2),
                'average_tonnes': round(avg_yield, 2)
            },
            'revenue': {
                'min_inr': round(min_revenue, 2),
                'max_inr': round(max_revenue, 2),
                'average_inr': round(avg_revenue, 2)
            },
            'investment_inr': round(total_investment, 2),
            'profit_estimate_inr': round(avg_revenue - total_investment, 2)
        }
    
    def calculate_months_to_harvest(self, crop_type: str, planting_month: int, 
                                     current_month: int = None) -> int:
        """
        Calculate months remaining until harvest
        
        Args:
            crop_type: 'Tomato', 'Grape', or 'Apple'
            planting_month: Month when crop was planted (1-12)
            current_month: Current month (defaults to actual current month)
            
        Returns:
            Number of months until harvest
        """
        if current_month is None:
            current_month = datetime.now().month
        
        if crop_type not in self.crop_data:
            return 0
        
        crop = self.crop_data[crop_type]
        seasons = crop['planting_seasons']
        
        # Find the matching season based on planting month
        for season_name, season_data in seasons.items():
            if planting_month in season_data['planting']:
                harvest_months = season_data['harvest']
                
                # Find next harvest month
                for harvest_month in sorted(harvest_months):
                    if harvest_month > current_month:
                        # Same year harvest
                        return harvest_month - current_month
                
                # Next year harvest
                if harvest_months:
                    first_harvest = min(harvest_months)
                    return (12 - current_month) + first_harvest
        
        # Default: assume 3-4 months for tomato, 4-5 for grape, 6-8 for apple
        defaults = {'Tomato': 3, 'Grape': 4, 'Apple': 6}
        return defaults.get(crop_type, 4)
    
    def calculate_disease_impact(self, crop_type: str, acres: float,
                                  planting_month: int, disease_name: str,
                                  months_to_harvest: int = None,
                                  current_month: int = None) -> Dict:
        """
        Calculate yield loss due to disease
        
        Args:
            crop_type: 'Tomato', 'Grape', or 'Apple'
            acres: Total planted acres
            planting_month: Month when crop was planted
            disease_name: Detected disease name
            months_to_harvest: Months until harvest (calculated if not provided)
            current_month: Current month for calculation
            
        Returns:
            Dict with yield loss calculations
        """
        if crop_type not in self.crop_data:
            return {'error': f'Unknown crop type: {crop_type}'}

        crop = self.crop_data[crop_type]
        
        # Get disease-specific spread rate
        spread_rates = crop['disease_spread_rate']
        spread_rate = self._get_disease_spread_rate(disease_name, spread_rates) / 100  # Convert to decimal

        # Calculate months to harvest if not provided
        if months_to_harvest is None:
            months_to_harvest = self.calculate_months_to_harvest(
                crop_type, planting_month, current_month
            )

        # Calculate total yield loss
        # Initial loss (12%) + monthly spread
        total_loss_percentage = INITIAL_DISEASE_IMPACT + (spread_rate * months_to_harvest)

        # Cap at 100% loss
        total_loss_percentage = min(total_loss_percentage, 1.0)
        
        # Calculate yield impact
        yield_info = crop['yield_per_acre']
        
        # For Apple, get yield based on farming type (default to traditional)
        if crop_type == 'Apple':
            avg_yield_per_acre = yield_info['traditional']['average']
        else:
            avg_yield_per_acre = yield_info['average']

        total_expected_yield = avg_yield_per_acre * acres  # tonnes
        lost_yield = total_expected_yield * total_loss_percentage
        salvageable_yield = total_expected_yield - lost_yield

        # Calculate economic loss
        price_info = crop['market_price_per_kg']
        
        # For Apple, use traditional price (default)
        if crop_type == 'Apple':
            avg_price = price_info['traditional']['average']
        else:
            avg_price = price_info.get('current') or price_info.get('average', 10)
        
        economic_loss = lost_yield * 1000 * avg_price  # Convert to kg
        expected_revenue = salvageable_yield * 1000 * avg_price
        
        # Treatment cost estimate (varies by crop and disease severity)
        treatment_cost_per_acre = {
            'Tomato': 5000,
            'Grape': 8000,
            'Apple': 6000
        }.get(crop_type, 5000)
        
        total_treatment_cost = treatment_cost_per_acre * acres
        
        return {
            'crop_type': crop_type,
            'disease': disease_name,
            'acres': acres,
            'planting_month': planting_month,
            'months_to_harvest': months_to_harvest,
            'yield_loss': {
                'initial_loss_percentage': INITIAL_DISEASE_IMPACT * 100,
                'monthly_spread_rate': spread_rate * 100,
                'total_loss_percentage': round(total_loss_percentage * 100, 2),
                'lost_yield_tonnes': round(lost_yield, 2),
                'salvageable_yield_tonnes': round(salvageable_yield, 2),
                'total_expected_yield_tonnes': round(total_expected_yield, 2)
            },
            'economic_impact': {
                'economic_loss_inr': round(economic_loss, 2),
                'expected_revenue_inr': round(expected_revenue, 2),
                'treatment_cost_inr': round(total_treatment_cost, 2),
                'net_revenue_after_treatment': round(expected_revenue - total_treatment_cost, 2)
            },
            'recommendation': self._get_treatment_recommendation(
                crop_type, total_loss_percentage, months_to_harvest
            )
        }
    
    def _get_treatment_recommendation(self, crop_type: str, 
                                       loss_percentage: float,
                                       months_to_harvest: int) -> str:
        """Generate treatment recommendation based on severity"""
        if loss_percentage <= 0.20:
            severity = "LOW"
            action = "Immediate treatment recommended. Good chance of recovery."
        elif loss_percentage <= 0.40:
            severity = "MODERATE"
            action = "Urgent treatment needed. Regular monitoring required."
        elif loss_percentage <= 0.60:
            severity = "HIGH"
            action = "Critical situation. Aggressive treatment and possible partial harvest."
        else:
            severity = "SEVERE"
            action = "Consider early harvest or crop removal to prevent spread."
        
        return (
            f"Severity: {severity} | {action} "
            f"Time to harvest: {months_to_harvest} months. "
            f"Act now to minimize losses!"
        )
    
    def get_location_recommendations(self, state: str, district: str = None) -> Dict:
        """Get location-specific recommendations"""
        recommendations = {}
        
        for crop_type, data in self.crop_data.items():
            if state in data['growing_states']:
                recommendations[crop_type] = {
                    'suitable': True,
                    'growing_regions': data.get('major_regions', {}).get(state, []),
                    'optimal_temp': data['optimal_temp']
                }
                
                # Check if district matches
                if district:
                    regions = data.get('major_regions', {}).get(state, [])
                    if any(district.lower() in region.lower() for region in regions):
                        recommendations[crop_type]['district_match'] = True
        
        return recommendations


# Singleton instance
_calculator = None

def get_yield_calculator():
    """Get or create calculator instance"""
    global _calculator
    if _calculator is None:
        _calculator = YieldCalculator()
    return _calculator
