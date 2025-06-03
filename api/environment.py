import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import WaterQualityEntry, Plant, PlantHealthLog

# Create logger
logger = logging.getLogger(__name__)

# Create blueprint
environment_bp = Blueprint('environment', __name__, url_prefix='/api')

# Water Quality Endpoints
@environment_bp.route('/water_quality_entries', methods=['GET'])
@jwt_required(optional=True)
def get_water_quality_entries():
    """Get water quality entries for the current user"""
    user_id = get_jwt_identity()
    
    # Handle query parameters for filtering
    filters = {}
    for key, value in request.args.items():
        if key.startswith('eq.'):
            field = key[3:]  # Remove 'eq.' prefix
            filters[field] = value
    
    # If user is authenticated, filter by user_id
    if user_id:
        entries = WaterQualityEntry.query.filter_by(user_id=user_id, **filters).all()
    else:
        # For demo purposes, return all entries if not authenticated
        entries = WaterQualityEntry.query.filter_by(**filters).all()
    
    return jsonify([entry.to_dict() for entry in entries])

@environment_bp.route('/water_quality_entries/<int:entry_id>', methods=['GET'])
@jwt_required(optional=True)
def get_water_quality_entry(entry_id):
    """Get a specific water quality entry"""
    user_id = get_jwt_identity()
    
    entry = WaterQualityEntry.query.get(entry_id)
    if not entry:
        return jsonify({"error": "Entry not found"}), 404
    
    # Check if user has access to this entry
    if user_id and entry.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    return jsonify(entry.to_dict())

@environment_bp.route('/water_quality_entries', methods=['POST'])
@jwt_required()
def create_water_quality_entry():
    """Create a new water quality entry"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    required_fields = ['location', 'ph_level', 'temperature', 'dissolved_oxygen', 'turbidity']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Create new entry
    entry = WaterQualityEntry(
        user_id=user_id,
        location=data['location'],
        ph_level=data['ph_level'],
        temperature=data['temperature'],
        dissolved_oxygen=data['dissolved_oxygen'],
        turbidity=data['turbidity'],
        notes=data.get('notes'),
        timestamp=data.get('timestamp', datetime.now().isoformat())
    )
    
    # Calculate if water is safe based on parameters
    # This is a simplified calculation - in a real app, this would be more complex
    entry.is_safe = (
        6.5 <= entry.ph_level <= 8.5 and
        entry.temperature <= 30 and
        entry.dissolved_oxygen >= 5 and
        entry.turbidity <= 5
    )
    
    db.session.add(entry)
    db.session.commit()
    
    return jsonify(entry.to_dict()), 201

@environment_bp.route('/water_quality_entries/<int:entry_id>', methods=['PATCH'])
@jwt_required()
def update_water_quality_entry(entry_id):
    """Update a water quality entry"""
    user_id = get_jwt_identity()
    data = request.json
    
    entry = WaterQualityEntry.query.get(entry_id)
    if not entry:
        return jsonify({"error": "Entry not found"}), 404
    
    # Check if user has access to this entry
    if entry.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Update fields
    for field in ['location', 'ph_level', 'temperature', 'dissolved_oxygen', 'turbidity', 'notes']:
        if field in data:
            setattr(entry, field, data[field])
    
    # Recalculate safety if relevant parameters were updated
    if any(param in data for param in ['ph_level', 'temperature', 'dissolved_oxygen', 'turbidity']):
        entry.is_safe = (
            6.5 <= entry.ph_level <= 8.5 and
            entry.temperature <= 30 and
            entry.dissolved_oxygen >= 5 and
            entry.turbidity <= 5
        )
    
    db.session.commit()
    
    return jsonify(entry.to_dict())

@environment_bp.route('/water_quality_entries/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def delete_water_quality_entry(entry_id):
    """Delete a water quality entry"""
    user_id = get_jwt_identity()
    
    entry = WaterQualityEntry.query.get(entry_id)
    if not entry:
        return jsonify({"error": "Entry not found"}), 404
    
    # Check if user has access to this entry
    if entry.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    db.session.delete(entry)
    db.session.commit()
    
    return jsonify({"message": "Entry deleted successfully"})

# Plant Endpoints
@environment_bp.route('/plants', methods=['GET'])
@jwt_required(optional=True)
def get_plants():
    """Get plants for the current user"""
    user_id = get_jwt_identity()
    
    # Handle query parameters for filtering
    filters = {}
    for key, value in request.args.items():
        if key.startswith('eq.'):
            field = key[3:]  # Remove 'eq.' prefix
            filters[field] = value
    
    # If user is authenticated, filter by user_id
    if user_id:
        plants = Plant.query.filter_by(user_id=user_id, **filters).all()
    else:
        # For demo purposes, return all plants if not authenticated
        plants = Plant.query.filter_by(**filters).all()
    
    return jsonify([plant.to_dict() for plant in plants])

@environment_bp.route('/plants/<int:plant_id>', methods=['GET'])
@jwt_required(optional=True)
def get_plant(plant_id):
    """Get a specific plant"""
    user_id = get_jwt_identity()
    
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    
    # Check if user has access to this plant
    if user_id and plant.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    return jsonify(plant.to_dict())

@environment_bp.route('/plants', methods=['POST'])
@jwt_required()
def create_plant():
    """Create a new plant"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'location']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Create new plant
    plant = Plant(
        user_id=user_id,
        name=data['name'],
        species=data.get('species'),
        location=data['location'],
        watering_schedule=data.get('watering_schedule'),
        sunlight_needs=data.get('sunlight_needs'),
        date_acquired=data.get('date_acquired', datetime.now().isoformat()),
        notes=data.get('notes'),
        image_url=data.get('image_url')
    )
    
    db.session.add(plant)
    db.session.commit()
    
    return jsonify(plant.to_dict()), 201

@environment_bp.route('/plants/<int:plant_id>', methods=['PATCH'])
@jwt_required()
def update_plant(plant_id):
    """Update a plant"""
    user_id = get_jwt_identity()
    data = request.json
    
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    
    # Check if user has access to this plant
    if plant.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Update fields
    for field in ['name', 'species', 'location', 'watering_schedule', 'sunlight_needs', 'notes', 'image_url']:
        if field in data:
            setattr(plant, field, data[field])
    
    db.session.commit()
    
    return jsonify(plant.to_dict())

@environment_bp.route('/plants/<int:plant_id>', methods=['DELETE'])
@jwt_required()
def delete_plant(plant_id):
    """Delete a plant"""
    user_id = get_jwt_identity()
    
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    
    # Check if user has access to this plant
    if plant.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    db.session.delete(plant)
    db.session.commit()
    
    return jsonify({"message": "Plant deleted successfully"})

@environment_bp.route('/plant_health_logs', methods=['GET'])
@jwt_required(optional=True)
def get_plant_health_logs():
    """Get plant health logs for the current user"""
    user_id = get_jwt_identity()
    
    # Get plant_id filter if provided
    plant_id = request.args.get('plant_id')
    
    # Build query
    query = PlantHealthLog.query
    
    if plant_id:
        query = query.filter_by(plant_id=plant_id)
    
    # If user is authenticated, filter by user_id
    if user_id:
        logs = query.filter_by(user_id=user_id).all()
    else:
        # For demo purposes, return all logs if not authenticated
        logs = query.all()
    
    return jsonify([log.to_dict() for log in logs])

@environment_bp.route('/plant_health_logs', methods=['POST'])
@jwt_required()
def create_plant_health_log():
    """Create a new plant health log"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    required_fields = ['plant_id', 'health_status']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if plant exists and belongs to user
    plant = Plant.query.get(data['plant_id'])
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    if plant.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Create new log
    log = PlantHealthLog(
        plant_id=data['plant_id'],
        user_id=user_id,
        health_status=data['health_status'],
        watered=data.get('watered', False),
        fertilized=data.get('fertilized', False),
        notes=data.get('notes'),
        image_url=data.get('image_url'),
        timestamp=data.get('timestamp', datetime.now().isoformat())
    )
    
    db.session.add(log)
    db.session.commit()
    
    return jsonify(log.to_dict()), 201

# RPC Functions
@environment_bp.route('/rpc/analyze_plant_health', methods=['POST'])
@jwt_required()
def analyze_plant_health():
    """Analyze plant health from an image"""
    user_id = get_jwt_identity()
    data = request.json
    
    # This would normally call an external API or ML model
    # For now, return a mock response
    analysis_result = {
        "health_score": 85,
        "issues": ["Minor leaf yellowing", "Slight soil dryness"],
        "recommendations": ["Water every 2-3 days", "Apply gentle fertilizer"],
        "confidence_score": 0.87
    }
    
    return jsonify(analysis_result)

@environment_bp.route('/rpc/get_water_safety', methods=['POST'])
@jwt_required()
def get_water_safety():
    """Get detailed water safety information"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate entry_id
    if 'entry_id' not in data:
        return jsonify({"error": "entry_id is required"}), 400
    
    # Get water quality entry
    entry = WaterQualityEntry.query.get(data['entry_id'])
    if not entry:
        return jsonify({"error": "Entry not found"}), 404
    
    # Check if user has access to this entry
    if entry.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Generate recommendations based on parameters
    recommendations = []
    
    if not (6.5 <= entry.ph_level <= 8.5):
        if entry.ph_level < 6.5:
            recommendations.append("pH is too acidic. Consider adding an alkaline treatment.")
        else:
            recommendations.append("pH is too alkaline. Consider adding an acid treatment.")
    
    if entry.temperature > 30:
        recommendations.append("Water temperature is too high. Implement cooling measures.")
    
    if entry.dissolved_oxygen < 5:
        recommendations.append("Dissolved oxygen is low. Consider adding aeration.")
    
    if entry.turbidity > 5:
        recommendations.append("Water is too turbid. Consider filtering or clarifying.")
    
    safety_info = {
        "is_safe": entry.is_safe,
        "recommendations": recommendations
    }
    
    return jsonify(safety_info)

@environment_bp.route('/rpc/get_watering_reminders', methods=['POST'])
@jwt_required()
def get_watering_reminders():
    """Get plant watering schedule reminders"""
    user_id = get_jwt_identity()
    
    # Get the user's plants
    plants = Plant.query.filter_by(user_id=user_id).all()
    
    # Generate watering reminders
    # In a real app, this would use actual watering schedules and last watered dates
    reminders = []
    for plant in plants:
        # Get the most recent watering log
        last_watering = PlantHealthLog.query.filter_by(
            plant_id=plant.id, 
            watered=True
        ).order_by(PlantHealthLog.timestamp.desc()).first()
        
        # Calculate due date based on last watering and watering schedule
        # This is a simplified version
        last_watered = last_watering.timestamp if last_watering else plant.date_acquired
        due_date = datetime.now().isoformat()  # Placeholder
        
        reminders.append({
            "plant_id": plant.id,
            "plant_name": plant.name,
            "last_watered": last_watered,
            "due_date": due_date
        })
    
    return jsonify(reminders)