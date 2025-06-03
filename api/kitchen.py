from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
import json
import base64
import uuid

from app import db
from models import User, GroceryReceipt, FridgeItem, BudgetLog

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
kitchen_bp = Blueprint('kitchen', __name__)

@kitchen_bp.route('/grocery/receipts', methods=['POST'])
@jwt_required()
def upload_grocery_receipt():
    """
    Upload and process a grocery receipt
    
    Required fields:
    - receipt_image: Base64 encoded image of receipt OR
    - items_json: JSON string of manually entered items
    
    Optional fields:
    - store_name: Name of the store
    - receipt_date: Date of receipt (ISO format)
    - total_amount: Total amount on receipt
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
        receipt_image = data.get('receipt_image')
        items_json = data.get('items_json')
        store_name = data.get('store_name')
        receipt_date_str = data.get('receipt_date')
        total_amount = data.get('total_amount')
        
        # Validate required fields
        if not receipt_image and not items_json:
            return jsonify({
                'status': 'error', 
                'message': 'Either receipt_image or items_json must be provided'
            }), 400
            
        # Parse receipt date if provided
        receipt_date = None
        if receipt_date_str:
            try:
                receipt_date = datetime.fromisoformat(receipt_date_str)
            except ValueError:
                return jsonify({
                    'status': 'error', 
                    'message': 'Invalid receipt_date format, use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }), 400
        else:
            receipt_date = datetime.utcnow()
        
        # If receipt image is provided, process it with OCR
        # This is just a placeholder - in production, use a proper OCR service
        if receipt_image:
            # In a real implementation, we'd process the image with OCR
            # For demo purposes, we'll just create some dummy data
            extracted_data = process_receipt_image(receipt_image)
            
            if not items_json:
                items_json = json.dumps(extracted_data['items'])
                
            if not store_name:
                store_name = extracted_data['store_name']
                
            if not total_amount:
                total_amount = extracted_data['total_amount']
        
        # Create grocery receipt
        receipt = GroceryReceipt()
        receipt.user_id = user.id
        receipt.store_name = store_name
        receipt.total_amount = float(total_amount) if total_amount else None
        receipt.receipt_date = receipt_date
        receipt.items_json = items_json
        receipt.ocr_confidence = 0.85 if receipt_image else None  # Placeholder
        
        # Add and commit
        db.session.add(receipt)
        db.session.commit()
        
        # Process items to add to fridge if items_json is provided
        items_added_to_fridge = 0
        try:
            if items_json:
                items = json.loads(items_json)
                for item in items:
                    # Add item to fridge if it has name, quantity, and unit
                    if all(k in item for k in ('name', 'quantity', 'unit')):
                        # Calculate expiry date based on category (placeholder logic)
                        category = item.get('category', 'general')
                        expiry_days = get_expiry_days(category)
                        expiry_date = datetime.utcnow() + timedelta(days=expiry_days)
                        
                        # Create fridge item
                        fridge_item = FridgeItem()
                        fridge_item.user_id = user.id
                        fridge_item.name = item['name']
                        fridge_item.category = category
                        fridge_item.quantity = float(item['quantity'])
                        fridge_item.unit = item['unit']
                        fridge_item.expiry_date = expiry_date
                        
                        db.session.add(fridge_item)
                        items_added_to_fridge += 1
                
                if items_added_to_fridge > 0:
                    db.session.commit()
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON format for items_json: {items_json}")
        except Exception as e:
            logger.error(f"Error adding items to fridge: {str(e)}")
            db.session.rollback()
        
        # Add to budget log if total amount is provided
        if total_amount:
            try:
                budget_log = BudgetLog()
                budget_log.user_id = user.id
                budget_log.category = 'groceries'
                budget_log.amount = float(total_amount)
                budget_log.description = f"Grocery shopping at {store_name}" if store_name else "Grocery shopping"
                
                db.session.add(budget_log)
                db.session.commit()
            except Exception as e:
                logger.error(f"Error adding budget log: {str(e)}")
                db.session.rollback()
        
        return jsonify({
            'status': 'success',
            'message': 'Grocery receipt uploaded successfully',
            'receipt_id': receipt.id,
            'items_added_to_fridge': items_added_to_fridge
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading grocery receipt: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while uploading grocery receipt'
        }), 500

@kitchen_bp.route('/grocery/receipts', methods=['GET'])
@jwt_required()
def get_grocery_receipts():
    """Get grocery receipts for the current user"""
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
        
        # Query receipts
        receipts = GroceryReceipt.query.filter_by(user_id=user.id)\
            .order_by(GroceryReceipt.created_at.desc())\
            .limit(limit).offset(offset).all()
            
        # Format response
        results = []
        for receipt in receipts:
            try:
                items = json.loads(receipt.items_json) if receipt.items_json else []
            except json.JSONDecodeError:
                items = []
                
            results.append({
                'id': receipt.id,
                'store_name': receipt.store_name,
                'total_amount': receipt.total_amount,
                'receipt_date': str(receipt.receipt_date) if receipt.receipt_date else None,
                'created_at': str(receipt.created_at),
                'items_count': len(items),
                'items': items[:5]  # Only include first 5 items to keep response size reasonable
            })
            
        return jsonify({
            'status': 'success',
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error getting grocery receipts: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving grocery receipts'
        }), 500

@kitchen_bp.route('/fridge', methods=['GET'])
@jwt_required()
def get_fridge_items():
    """Get fridge items for the current user"""
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
        category = request.args.get('category')
        expiring_within_days = request.args.get('expiring_within_days', type=int)
        
        # Build query
        query = FridgeItem.query.filter_by(user_id=user.id)
        
        if category:
            query = query.filter_by(category=category)
            
        if expiring_within_days:
            expiry_cutoff = datetime.utcnow() + timedelta(days=expiring_within_days)
            query = query.filter(FridgeItem.expiry_date <= expiry_cutoff)
            
        # Execute query
        items = query.order_by(FridgeItem.expiry_date.asc()).all()
            
        # Format response
        results = []
        for item in items:
            # Calculate days until expiry
            days_until_expiry = None
            if item.expiry_date:
                delta = item.expiry_date - datetime.utcnow()
                days_until_expiry = delta.days
                
            results.append({
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'quantity': item.quantity,
                'unit': item.unit,
                'expiry_date': str(item.expiry_date) if item.expiry_date else None,
                'days_until_expiry': days_until_expiry,
                'created_at': str(item.created_at),
                'updated_at': str(item.updated_at) if item.updated_at else None
            })
            
        return jsonify({
            'status': 'success',
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error getting fridge items: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving fridge items'
        }), 500

@kitchen_bp.route('/fridge/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_fridge_item(item_id):
    """
    Update a fridge item
    
    Optional fields to update:
    - name: Item name
    - category: Item category
    - quantity: Item quantity
    - unit: Unit of measurement
    - expiry_date: Expiry date (ISO format)
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
            
        # Find item
        item = FridgeItem.query.filter_by(id=item_id, user_id=user.id).first()
        
        if not item:
            return jsonify({
                'status': 'error', 
                'message': 'Item not found'
            }), 404
            
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error', 
                'message': 'No data provided'
            }), 400
            
        # Update fields if provided
        if 'name' in data:
            item.name = data['name']
            
        if 'category' in data:
            item.category = data['category']
            
        if 'quantity' in data:
            try:
                item.quantity = float(data['quantity'])
            except ValueError:
                return jsonify({
                    'status': 'error', 
                    'message': 'Quantity must be a number'
                }), 400
                
        if 'unit' in data:
            item.unit = data['unit']
            
        if 'expiry_date' in data:
            try:
                item.expiry_date = datetime.fromisoformat(data['expiry_date'])
            except ValueError:
                return jsonify({
                    'status': 'error', 
                    'message': 'Invalid expiry_date format, use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }), 400
        
        # Update timestamp
        item.updated_at = datetime.utcnow()
        
        # Commit changes
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Fridge item updated successfully',
            'item_id': item.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating fridge item: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating fridge item'
        }), 500

@kitchen_bp.route('/fridge/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_fridge_item(item_id):
    """Delete a fridge item"""
    try:
        # Get user ID from JWT token
        user_uid = get_jwt_identity()
        user = User.query.filter_by(uid=user_uid).first()
        
        if not user:
            return jsonify({
                'status': 'error', 
                'message': 'User not found'
            }), 404
            
        # Find item
        item = FridgeItem.query.filter_by(id=item_id, user_id=user.id).first()
        
        if not item:
            return jsonify({
                'status': 'error', 
                'message': 'Item not found'
            }), 404
            
        # Delete item
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Fridge item deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting fridge item: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting fridge item'
        }), 500

# Helper functions
def process_receipt_image(receipt_image_base64):
    """
    Process a receipt image with OCR to extract information
    
    This is a placeholder implementation - in production, use a proper OCR service
    """
    # In a real implementation, we'd decode the base64 image and use OCR
    # For now, we'll just return some dummy data
    
    # Simplified example return
    return {
        'store_name': 'EcoMart',
        'total_amount': 825.50,
        'receipt_date': datetime.utcnow().isoformat(),
        'items': [
            {'name': 'Organic Apples', 'quantity': 1.2, 'unit': 'kg', 'price': 150, 'category': 'fruits'},
            {'name': 'Whole Wheat Bread', 'quantity': 1, 'unit': 'loaf', 'price': 75, 'category': 'bakery'},
            {'name': 'Almond Milk', 'quantity': 1, 'unit': 'liter', 'price': 120, 'category': 'dairy_alternative'},
            {'name': 'Quinoa', 'quantity': 0.5, 'unit': 'kg', 'price': 200, 'category': 'grains'},
            {'name': 'Spinach', 'quantity': 1, 'unit': 'bunch', 'price': 60, 'category': 'vegetables'},
            {'name': 'Tofu', 'quantity': 1, 'unit': 'pack', 'price': 80, 'category': 'protein'},
            {'name': 'Eco-friendly Dish Soap', 'quantity': 1, 'unit': 'bottle', 'price': 140.50, 'category': 'household'}
        ]
    }

def get_expiry_days(category):
    """
    Get the number of days until expiry based on food category
    
    This is a placeholder implementation with simplified rules
    """
    # Simplified expiry rules based on category
    expiry_rules = {
        'fruits': 7,
        'vegetables': 7,
        'dairy': 10,
        'dairy_alternative': 14,
        'meat': 3,
        'seafood': 2,
        'bakery': 5,
        'grains': 180,
        'canned': 365,
        'frozen': 90,
        'snacks': 90,
        'beverages': 30,
        'condiments': 180,
        'spices': 365,
        'protein': 5,
        'household': 365,
        'general': 14  # Default
    }
    
    return expiry_rules.get(category.lower(), 14)  # Default to 14 days