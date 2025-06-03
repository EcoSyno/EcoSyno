from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
import json
import uuid

from app import db
from models import User, LaundryLog

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
wardrobe_bp = Blueprint('wardrobe', __name__)

@wardrobe_bp.route('/suggest-outfit', methods=['GET'])
@jwt_required()
def suggest_outfit():
    """
    Suggest an outfit based on various parameters
    
    Query parameters:
    - weather: Current weather (e.g., 'sunny', 'rainy', 'cold')
    - occasion: Occasion type (e.g., 'casual', 'formal', 'workout')
    - season: Current season (optional)
    """
    try:
        # Get user ID from JWT token
        user_uid = get_jwt_identity()
        user = User.query.filter_by(uid=user_uid).first()
        
        if not user:
            return jsonify({
                'status': 'error', 
                'message': 'User not found'
            }), 404
            
        # Get query parameters
        weather = request.args.get('weather', 'moderate')
        occasion = request.args.get('occasion', 'casual')
        season = request.args.get('season')
        
        # Determine season if not provided
        if not season:
            # Simplified season determination based on month
            month = datetime.utcnow().month
            if month in [12, 1, 2]:
                season = 'winter'
            elif month in [3, 4, 5]:
                season = 'spring'
            elif month in [6, 7, 8]:
                season = 'summer'
            else:
                season = 'fall'
        
        # In a real implementation, this would use user's wardrobe data
        # and potentially an AI model to suggest appropriate outfits
        # For now, we'll return pre-defined suggestions based on parameters
        
        # Simplified outfit suggestions
        outfit_suggestions = {
            'winter': {
                'sunny': {
                    'casual': {
                        'top': 'Light sweater or long-sleeve shirt',
                        'bottom': 'Jeans or casual pants',
                        'outerwear': 'Light jacket',
                        'accessories': 'Sunglasses',
                        'footwear': 'Casual shoes or boots'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse',
                        'bottom': 'Dress pants or skirt',
                        'outerwear': 'Wool coat or blazer',
                        'accessories': 'Scarf, formal watch',
                        'footwear': 'Formal shoes'
                    },
                    'workout': {
                        'top': 'Thermal compression shirt',
                        'bottom': 'Thermal leggings or track pants',
                        'outerwear': 'Light running jacket',
                        'accessories': 'Beanie, gloves',
                        'footwear': 'Running shoes'
                    }
                },
                'rainy': {
                    'casual': {
                        'top': 'Long-sleeve shirt',
                        'bottom': 'Water-resistant pants',
                        'outerwear': 'Rain jacket or waterproof coat',
                        'accessories': 'Umbrella, waterproof hat',
                        'footwear': 'Waterproof boots'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse',
                        'bottom': 'Dress pants or skirt',
                        'outerwear': 'Waterproof trench coat',
                        'accessories': 'Umbrella, formal watch',
                        'footwear': 'Water-resistant formal shoes'
                    },
                    'workout': {
                        'top': 'Water-resistant compression shirt',
                        'bottom': 'Water-resistant leggings or track pants',
                        'outerwear': 'Waterproof running jacket',
                        'accessories': 'Waterproof hat',
                        'footwear': 'Water-resistant running shoes'
                    }
                },
                'cold': {
                    'casual': {
                        'top': 'Thermal shirt, heavy sweater',
                        'bottom': 'Insulated jeans or thermal pants',
                        'outerwear': 'Heavy winter coat',
                        'accessories': 'Beanie, scarf, gloves',
                        'footwear': 'Insulated winter boots'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse, wool sweater',
                        'bottom': 'Wool dress pants or skirt',
                        'outerwear': 'Wool coat',
                        'accessories': 'Cashmere scarf, leather gloves',
                        'footwear': 'Insulated formal shoes or boots'
                    },
                    'workout': {
                        'top': 'Heavy thermal compression shirt',
                        'bottom': 'Heavy thermal leggings or track pants',
                        'outerwear': 'Insulated running jacket',
                        'accessories': 'Thermal beanie, thermal gloves',
                        'footwear': 'Insulated running shoes'
                    }
                }
            },
            'spring': {
                'sunny': {
                    'casual': {
                        'top': 'T-shirt or light long-sleeve',
                        'bottom': 'Jeans or casual pants',
                        'outerwear': 'Light jacket or cardigan',
                        'accessories': 'Sunglasses',
                        'footwear': 'Sneakers or casual shoes'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse',
                        'bottom': 'Dress pants, skirt, or light dress',
                        'outerwear': 'Light blazer',
                        'accessories': 'Light scarf, watch',
                        'footwear': 'Formal shoes'
                    },
                    'workout': {
                        'top': 'Light moisture-wicking shirt',
                        'bottom': 'Running shorts or leggings',
                        'outerwear': 'Light running jacket',
                        'accessories': 'Cap',
                        'footwear': 'Running shoes'
                    }
                },
                'rainy': {
                    'casual': {
                        'top': 'Long-sleeve shirt',
                        'bottom': 'Jeans or casual pants',
                        'outerwear': 'Rain jacket',
                        'accessories': 'Umbrella',
                        'footwear': 'Water-resistant shoes or boots'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse',
                        'bottom': 'Dress pants or skirt',
                        'outerwear': 'Trench coat',
                        'accessories': 'Umbrella, watch',
                        'footwear': 'Water-resistant formal shoes'
                    },
                    'workout': {
                        'top': 'Water-resistant shirt',
                        'bottom': 'Water-resistant leggings or pants',
                        'outerwear': 'Water-resistant running jacket',
                        'accessories': 'Waterproof cap',
                        'footwear': 'Water-resistant running shoes'
                    }
                },
                'cold': {
                    'casual': {
                        'top': 'Long-sleeve shirt, light sweater',
                        'bottom': 'Jeans or casual pants',
                        'outerwear': 'Medium jacket',
                        'accessories': 'Light scarf',
                        'footwear': 'Casual shoes or light boots'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse',
                        'bottom': 'Dress pants or skirt',
                        'outerwear': 'Light wool coat or blazer',
                        'accessories': 'Light scarf, watch',
                        'footwear': 'Formal shoes'
                    },
                    'workout': {
                        'top': 'Thermal compression shirt',
                        'bottom': 'Thermal leggings or pants',
                        'outerwear': 'Running jacket',
                        'accessories': 'Light beanie',
                        'footwear': 'Running shoes'
                    }
                }
            },
            'summer': {
                'sunny': {
                    'casual': {
                        'top': 'T-shirt or tank top',
                        'bottom': 'Shorts or light pants',
                        'outerwear': 'None',
                        'accessories': 'Sunglasses, cap',
                        'footwear': 'Sandals or sneakers'
                    },
                    'formal': {
                        'top': 'Short-sleeve dress shirt or blouse',
                        'bottom': 'Light dress pants, skirt, or summer dress',
                        'outerwear': 'Light blazer (optional)',
                        'accessories': 'Sunglasses, minimal jewelry',
                        'footwear': 'Light formal shoes'
                    },
                    'workout': {
                        'top': 'Moisture-wicking tank or t-shirt',
                        'bottom': 'Running shorts',
                        'outerwear': 'None',
                        'accessories': 'Cap, sweatbands',
                        'footwear': 'Running shoes'
                    }
                },
                'rainy': {
                    'casual': {
                        'top': 'T-shirt',
                        'bottom': 'Light pants',
                        'outerwear': 'Light rain jacket',
                        'accessories': 'Umbrella',
                        'footwear': 'Water-resistant shoes'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse',
                        'bottom': 'Dress pants, skirt, or dress',
                        'outerwear': 'Light trench coat',
                        'accessories': 'Umbrella',
                        'footwear': 'Water-resistant formal shoes'
                    },
                    'workout': {
                        'top': 'Moisture-wicking shirt',
                        'bottom': 'Water-resistant shorts or leggings',
                        'outerwear': 'Light water-resistant jacket',
                        'accessories': 'Waterproof cap',
                        'footwear': 'Water-resistant running shoes'
                    }
                },
                'cold': {
                    'casual': {
                        'top': 'T-shirt or light long-sleeve',
                        'bottom': 'Light pants',
                        'outerwear': 'Light jacket',
                        'accessories': 'None',
                        'footwear': 'Sneakers or light shoes'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse',
                        'bottom': 'Dress pants, skirt, or dress',
                        'outerwear': 'Light blazer',
                        'accessories': 'Minimal jewelry',
                        'footwear': 'Formal shoes'
                    },
                    'workout': {
                        'top': 'Moisture-wicking shirt',
                        'bottom': 'Running shorts or light leggings',
                        'outerwear': 'Light running jacket',
                        'accessories': 'None',
                        'footwear': 'Running shoes'
                    }
                }
            },
            'fall': {
                'sunny': {
                    'casual': {
                        'top': 'Long-sleeve shirt or light sweater',
                        'bottom': 'Jeans or casual pants',
                        'outerwear': 'Light jacket',
                        'accessories': 'Sunglasses',
                        'footwear': 'Casual shoes or boots'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse',
                        'bottom': 'Dress pants or skirt',
                        'outerwear': 'Blazer or light coat',
                        'accessories': 'Light scarf, watch',
                        'footwear': 'Formal shoes'
                    },
                    'workout': {
                        'top': 'Long-sleeve moisture-wicking shirt',
                        'bottom': 'Running pants or leggings',
                        'outerwear': 'Light running jacket',
                        'accessories': 'Cap',
                        'footwear': 'Running shoes'
                    }
                },
                'rainy': {
                    'casual': {
                        'top': 'Long-sleeve shirt',
                        'bottom': 'Jeans or casual pants',
                        'outerwear': 'Rain jacket',
                        'accessories': 'Umbrella',
                        'footwear': 'Water-resistant shoes or boots'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse',
                        'bottom': 'Dress pants or skirt',
                        'outerwear': 'Trench coat',
                        'accessories': 'Umbrella, watch',
                        'footwear': 'Water-resistant formal shoes'
                    },
                    'workout': {
                        'top': 'Water-resistant long-sleeve shirt',
                        'bottom': 'Water-resistant pants or leggings',
                        'outerwear': 'Water-resistant running jacket',
                        'accessories': 'Waterproof cap',
                        'footwear': 'Water-resistant running shoes'
                    }
                },
                'cold': {
                    'casual': {
                        'top': 'Sweater',
                        'bottom': 'Jeans or casual pants',
                        'outerwear': 'Medium jacket',
                        'accessories': 'Scarf, beanie',
                        'footwear': 'Boots'
                    },
                    'formal': {
                        'top': 'Dress shirt or blouse, sweater',
                        'bottom': 'Dress pants or skirt',
                        'outerwear': 'Wool coat',
                        'accessories': 'Scarf, gloves',
                        'footwear': 'Formal shoes or boots'
                    },
                    'workout': {
                        'top': 'Thermal compression shirt',
                        'bottom': 'Thermal leggings or pants',
                        'outerwear': 'Running jacket',
                        'accessories': 'Beanie, gloves',
                        'footwear': 'Running shoes'
                    }
                }
            }
        }
        
        # Get suggestion
        try:
            suggestion = outfit_suggestions[season][weather][occasion]
        except KeyError:
            # Handle unknown parameters
            return jsonify({
                'status': 'error',
                'message': f'No suggestion available for {season} {weather} {occasion}',
                'available_params': {
                    'seasons': list(outfit_suggestions.keys()),
                    'weather': list(outfit_suggestions['summer'].keys()),
                    'occasions': list(outfit_suggestions['summer']['sunny'].keys())
                }
            }), 400
        
        # Format response
        result = {
            'season': season,
            'weather': weather,
            'occasion': occasion,
            'outfit': suggestion,
            'sustainability_tips': [
                'Choose natural fabrics for better breathability',
                'Layer for versatility and extended wear',
                'Consider eco-friendly brands for new purchases'
            ]
        }
            
        return jsonify({
            'status': 'success',
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error suggesting outfit: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while suggesting outfit'
        }), 500

@wardrobe_bp.route('/laundry', methods=['POST'])
@jwt_required()
def log_laundry():
    """
    Record a laundry session
    
    Required fields:
    - wash_type: Type of wash (e.g., 'normal', 'eco', 'quick')
    - item_count: Number of items washed
    
    Optional fields:
    - notes: Additional notes
    """
    try:
        # Get user ID from JWT token
        user_uid = get_jwt_identity()
        user = User.query.filter_by(uid=user_uid).first()
        
        if not user:
            return jsonify({
                'status': 'error', 
                'message': 'User not found'
            }), 404
            
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error', 
                'message': 'No data provided'
            }), 400
            
        # Get fields
        wash_type = data.get('wash_type')
        item_count = data.get('item_count')
        notes = data.get('notes')
        
        # Validate required fields
        if not wash_type:
            return jsonify({
                'status': 'error', 
                'message': 'Wash type is required'
            }), 400
        
        if not item_count:
            return jsonify({
                'status': 'error', 
                'message': 'Item count is required'
            }), 400
            
        try:
            item_count = int(item_count)
        except ValueError:
            return jsonify({
                'status': 'error', 
                'message': 'Item count must be a number'
            }), 400
        
        # Create laundry log
        laundry_log = LaundryLog()
        laundry_log.user_id = user.id
        laundry_log.wash_type = wash_type
        laundry_log.item_count = item_count
        laundry_log.notes = notes
        
        # Add and commit
        db.session.add(laundry_log)
        db.session.commit()
        
        # Calculate eco impact stats
        water_saved = 0
        energy_saved = 0
        
        if wash_type.lower() == 'eco':
            # Eco wash typically saves about 30% water and 40% energy
            water_saved = item_count * 5  # 5 liters per item
            energy_saved = item_count * 0.1  # 0.1 kWh per item
        elif wash_type.lower() == 'quick':
            # Quick wash typically saves about 20% water and 10% energy
            water_saved = item_count * 3  # 3 liters per item
            energy_saved = item_count * 0.05  # 0.05 kWh per item
        
        return jsonify({
            'status': 'success',
            'message': 'Laundry session recorded successfully',
            'laundry_id': laundry_log.id,
            'eco_impact': {
                'water_saved': water_saved,
                'energy_saved': energy_saved,
                'carbon_footprint_reduced': energy_saved * 0.5  # 0.5 kg CO2 per kWh
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging laundry: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while logging laundry'
        }), 500

@wardrobe_bp.route('/laundry', methods=['GET'])
@jwt_required()
def get_laundry_logs():
    """Get laundry logs for the current user"""
    try:
        # Get user ID from JWT token
        user_uid = get_jwt_identity()
        user = User.query.filter_by(uid=user_uid).first()
        
        if not user:
            return jsonify({
                'status': 'error', 
                'message': 'User not found'
            }), 404
            
        # Get optional query parameters
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Query logs
        logs = LaundryLog.query.filter_by(user_id=user.id)\
            .order_by(LaundryLog.created_at.desc())\
            .limit(limit).offset(offset).all()
            
        # Format response
        results = []
        for log in logs:
            # Calculate eco impact stats
            water_saved = 0
            energy_saved = 0
            
            if log.wash_type.lower() == 'eco':
                # Eco wash typically saves about 30% water and 40% energy
                water_saved = log.item_count * 5  # 5 liters per item
                energy_saved = log.item_count * 0.1  # 0.1 kWh per item
            elif log.wash_type.lower() == 'quick':
                # Quick wash typically saves about 20% water and 10% energy
                water_saved = log.item_count * 3  # 3 liters per item
                energy_saved = log.item_count * 0.05  # 0.05 kWh per item
                
            results.append({
                'id': log.id,
                'wash_type': log.wash_type,
                'item_count': log.item_count,
                'notes': log.notes,
                'created_at': str(log.created_at),
                'eco_impact': {
                    'water_saved': water_saved,
                    'energy_saved': energy_saved,
                    'carbon_footprint_reduced': energy_saved * 0.5  # 0.5 kg CO2 per kWh
                }
            })
            
        # Calculate aggregated stats
        total_washes = len(results)
        total_items = sum(log['item_count'] for log in results)
        total_water_saved = sum(log['eco_impact']['water_saved'] for log in results)
        total_energy_saved = sum(log['eco_impact']['energy_saved'] for log in results)
        total_carbon_reduced = sum(log['eco_impact']['carbon_footprint_reduced'] for log in results)
            
        return jsonify({
            'status': 'success',
            'count': total_washes,
            'results': results,
            'aggregated_stats': {
                'total_washes': total_washes,
                'total_items': total_items,
                'total_water_saved': total_water_saved,
                'total_energy_saved': total_energy_saved,
                'total_carbon_reduced': total_carbon_reduced
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting laundry logs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving laundry logs'
        }), 500

@wardrobe_bp.route('/condition', methods=['GET'])
@jwt_required()
def get_wardrobe_condition():
    """
    Get overall wardrobe condition and statistics
    
    In a real implementation, this would use data from the user's wardrobe items
    For now, we'll return placeholder statistics
    """
    try:
        # Get user ID from JWT token
        user_uid = get_jwt_identity()
        user = User.query.filter_by(uid=user_uid).first()
        
        if not user:
            return jsonify({
                'status': 'error', 
                'message': 'User not found'
            }), 404
            
        # Get laundry logs for calculating stats
        logs = LaundryLog.query.filter_by(user_id=user.id).all()
        
        # Calculate wash frequency (washes per week)
        # Calculate based on the last 4 weeks
        recent_logs = [log for log in logs if log.created_at >= datetime.utcnow() - timedelta(days=28)]
        wash_frequency = len(recent_logs) / 4 if len(recent_logs) > 0 else 0
        
        # Format response with placeholder data
        # In a real implementation, this would use actual wardrobe data
        result = {
            'overall_condition': 'good',
            'item_count': {
                'total': 57,
                'by_category': {
                    'tops': 18,
                    'bottoms': 12,
                    'dresses': 5,
                    'outerwear': 8,
                    'accessories': 14
                }
            },
            'statistics': {
                'wash_frequency': wash_frequency,
                'most_worn_categories': ['tops', 'bottoms'],
                'least_worn_categories': ['formal', 'outerwear'],
                'average_item_age': 2.7  # years
            },
            'sustainability_score': {
                'overall': 82,  # 0-100
                'components': {
                    'material_composition': 75,
                    'usage_efficiency': 90,
                    'care_practices': 85
                }
            },
            'suggestions': [
                'Consider donating or upcycling rarely worn items',
                'Look for sustainable alternatives when replacing worn-out basics',
                'Continue using eco-friendly wash modes for optimal garment life'
            ]
        }
            
        return jsonify({
            'status': 'success',
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error getting wardrobe condition: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving wardrobe condition'
        }), 500