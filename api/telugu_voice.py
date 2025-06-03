"""
Telugu Voice API

Provides API endpoints for generating and managing Telugu voice audio files.
"""

import os
import shutil
import json
from flask import Blueprint, request, jsonify, current_app

# Create the blueprint
telugu_voice_api = Blueprint('telugu_voice_api', __name__)

@telugu_voice_api.route('/api/create_audio_directories', methods=['POST'])
def create_audio_directories():
    """
    Create directories for storing Telugu audio files.
    This is needed for the native Telugu voice implementation.
    """
    # Verify user is admin
    # Note: In production, use proper authentication here
    
    # Get directories from request
    data = request.json
    directories = data.get('directories', [])
    
    created = []
    errors = []
    
    for directory in directories:
        # Ensure path is safe
        if '..' in directory or not directory.startswith('/static/'):
            errors.append(f"Invalid path: {directory}")
            continue
        
        # Create full path
        full_path = os.path.join(os.getcwd(), directory.lstrip('/'))
        
        try:
            # Create directory if it doesn't exist
            if not os.path.exists(full_path):
                os.makedirs(full_path)
                created.append(directory)
            else:
                created.append(f"{directory} (already exists)")
        except Exception as e:
            errors.append(f"{directory}: {str(e)}")
    
    return jsonify({
        'status': 'success' if not errors else 'partial',
        'created': created,
        'errors': errors
    })

@telugu_voice_api.route('/api/telugu_audio', methods=['GET'])
def list_telugu_audio():
    """
    List available Telugu audio files.
    """
    # Path for Telugu audio files
    audio_path = os.path.join(os.getcwd(), 'static', 'audio', 'telugu')
    
    # Check if directory exists
    if not os.path.exists(audio_path):
        return jsonify({
            'status': 'error',
            'message': 'Telugu audio directory does not exist',
            'files': []
        })
    
    # Get list of audio files
    files = []
    try:
        for filename in os.listdir(audio_path):
            if filename.endswith(('.mp3', '.wav', '.ogg')):
                files.append({
                    'filename': filename,
                    'path': f'/static/audio/telugu/{filename}'
                })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'files': []
        })
    
    return jsonify({
        'status': 'success',
        'files': files
    })

def register_telugu_voice_routes(app):
    """
    Register the Telugu voice API routes with the Flask app.
    """
    app.register_blueprint(telugu_voice_api)
    print("Telugu voice API registered successfully")