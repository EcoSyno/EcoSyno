from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime
import json
import uuid

from app import db
from models import User, MarketplaceItem, MarketplaceOrder
from utils import validate_cart, generate_order_number, validate_delivery_hub

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
marketplace_bp = Blueprint('marketplace', __name__)

@marketplace_bp.route('/items', methods=['GET'])
def get_marketplace_items():
    """
    Get list of marketplace items
    
    Query parameters:
    - category: Filter by category
    - limit: Limit number of items (default 20)
    - offset: Offset for pagination (default 0)
    """
    try:
        # Get query parameters
        category = request.args.get('category')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = MarketplaceItem.query.filter_by(is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        # Execute query with pagination
        items = query.limit(limit).offset(offset).all()
        
        # Format response
        results = []
        for item in items:
            results.append({
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'price': item.price,
                'stock': item.stock,
                'category': item.category,
                'image_url': item.image_url
            })
            
        return jsonify({
            'status': 'success',
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error getting marketplace items: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving marketplace items'
        }), 500

@marketplace_bp.route('/orders', methods=['POST'])
@jwt_required()
def place_order():
    """
    Place a new order
    
    Required fields:
    - items: Array of objects with item_id and quantity
    - delivery_hub: Delivery hub identifier
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
            
        # Get required fields
        items_data = data.get('items')
        delivery_hub = data.get('delivery_hub')
        
        # Validate required fields
        if not items_data or not isinstance(items_data, list) or len(items_data) == 0:
            return jsonify({
                'status': 'error', 
                'message': 'Items array is required and must not be empty'
            }), 400
            
        if not delivery_hub:
            return jsonify({
                'status': 'error', 
                'message': 'Delivery hub is required'
            }), 400
            
        # Validate delivery hub
        if not validate_delivery_hub(delivery_hub):
            return jsonify({
                'status': 'error', 
                'message': 'Invalid delivery hub'
            }), 400
            
        # Calculate total and validate cart
        item_ids = [item.get('item_id') for item in items_data]
        items = MarketplaceItem.query.filter(MarketplaceItem.id.in_(item_ids)).all()
        
        if len(items) != len(item_ids):
            return jsonify({
                'status': 'error', 
                'message': 'One or more items not found'
            }), 400
            
        # Build cart for validation
        cart = []
        total_amount = 0
        
        for item_data in items_data:
            item_id = item_data.get('item_id')
            quantity = item_data.get('quantity', 1)
            
            # Find item
            item = next((i for i in items if i.id == item_id), None)
            
            if not item:
                return jsonify({
                    'status': 'error', 
                    'message': f'Item with ID {item_id} not found'
                }), 400
                
            # Check stock
            if item.stock < quantity:
                return jsonify({
                    'status': 'error', 
                    'message': f'Not enough stock for {item.name}, only {item.stock} available'
                }), 400
                
            # Add to cart
            cart.append({
                'item_id': item_id,
                'quantity': quantity,
                'price': item.price
            })
            
            # Update total
            total_amount += item.price * quantity
            
        # Create order
        order_number = generate_order_number()
        
        order = MarketplaceOrder()
        order.user_id = user.id
        order.order_number = order_number
        order.total_amount = total_amount
        order.status = 'pending'
        order.delivery_hub = delivery_hub
        
        db.session.add(order)
        db.session.flush()  # Get order ID without committing
        
        # Create order items array
        order_items = []
        for cart_item in cart:
            order_items.append({
                'item_id': cart_item['item_id'],
                'quantity': cart_item['quantity'],
                'price': cart_item['price']
            })
            
        # Set order items
        order.items = order_items
        
        # Update stock for each item
        for cart_item in cart:
            item = next((i for i in items if i.id == cart_item['item_id']), None)
            if item:
                item.stock -= cart_item['quantity']
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Order placed successfully',
            'order_number': order_number,
            'total_amount': total_amount
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error placing order: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while placing order'
        }), 500

@marketplace_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Get orders for the current user"""
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
        
        # Query orders
        orders = MarketplaceOrder.query.filter_by(user_id=user.id)\
            .order_by(MarketplaceOrder.created_at.desc())\
            .limit(limit).offset(offset).all()
            
        # Format response
        results = []
        for order in orders:
            results.append({
                'id': order.id,
                'order_number': order.order_number,
                'total_amount': order.total_amount,
                'status': order.status,
                'delivery_hub': order.delivery_hub,
                'created_at': str(order.created_at),
                'updated_at': str(order.updated_at) if order.updated_at else None
            })
            
        return jsonify({
            'status': 'success',
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving orders'
        }), 500

@marketplace_bp.route('/orders/<order_number>', methods=['GET'])
@jwt_required()
def get_order_details(order_number):
    """Get details for a specific order"""
    try:
        # Get user ID from JWT token
        user_uid = get_jwt_identity()
        user = User.query.filter_by(uid=user_uid).first()
        
        if not user:
            return jsonify({
                'status': 'error', 
                'message': 'User not found'
            }), 404
            
        # Find order
        order = MarketplaceOrder.query.filter_by(
            user_id=user.id, 
            order_number=order_number
        ).first()
        
        if not order:
            return jsonify({
                'status': 'error', 
                'message': 'Order not found'
            }), 404
            
        # Get order items from JSON field
        order_items = order.items if order.items else []
        
        # Format items
        items = []
        for order_item in order_items:
            item_id = order_item.get('item_id')
            item = MarketplaceItem.query.get(item_id) if item_id else None
            quantity = order_item.get('quantity', 0)
            price = order_item.get('price', 0)
            items.append({
                'item_id': item_id,
                'item_name': item.name if item else 'Unknown',
                'quantity': quantity,
                'price': price,
                'subtotal': quantity * price
            })
            
        # Format response
        result = {
            'id': order.id,
            'order_number': order.order_number,
            'total_amount': order.total_amount,
            'status': order.status,
            'delivery_hub': order.delivery_hub,
            'created_at': str(order.created_at),
            'updated_at': str(order.updated_at) if order.updated_at else None,
            'items': items
        }
            
        return jsonify({
            'status': 'success',
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error getting order details: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving order details'
        }), 500

@marketplace_bp.route('/delivery-hubs', methods=['GET'])
@jwt_required()
def get_delivery_hubs():
    """Get list of available delivery hubs"""
    try:
        # This would typically come from a database
        # For now, we'll return a static list
        hubs = [
            {
                'id': 'hub_01',
                'name': 'Green Commons Hub',
                'address': '123 Eco Street, Sustainableville',
                'capacity': 500
            },
            {
                'id': 'hub_02',
                'name': 'EcoVillage Center',
                'address': '45 Renewable Road, Greentown',
                'capacity': 350
            },
            {
                'id': 'hub_03',
                'name': 'Sustainable Square',
                'address': '78 Recycling Avenue, Ecotropolis',
                'capacity': 400
            }
        ]
            
        return jsonify({
            'status': 'success',
            'count': len(hubs),
            'results': hubs
        })
        
    except Exception as e:
        logger.error(f"Error getting delivery hubs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving delivery hubs'
        }), 500

# Admin-only endpoints would go here, requiring role validation