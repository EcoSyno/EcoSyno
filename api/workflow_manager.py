"""
N8N Workflow Manager API Module for EcoSyno

This module provides an interface to manage N8N workflows within the EcoSyno application.
It allows creating, retrieving, updating, and executing workflows.
"""

import os
import json
import logging
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from auth_middleware import admin_required

# Initialize blueprint
workflow_bp = Blueprint('workflow', __name__)

# Configure logging
logger = logging.getLogger(__name__)

# N8N API Configuration
N8N_BASE_URL = os.environ.get('N8N_BASE_URL', 'http://localhost:5678')
N8N_API_KEY = os.environ.get('N8N_API_KEY', '')

# Helper Functions
def n8n_api_request(endpoint, method='GET', data=None, params=None):
    """Make requests to the N8N API with proper authentication"""
    headers = {
        'Content-Type': 'application/json',
        'X-N8N-API-KEY': N8N_API_KEY
    }
    
    url = f"{N8N_BASE_URL}/api/v1/{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request to N8N API: {str(e)}")
        return None

# API Endpoints

@workflow_bp.route('/health', methods=['GET'])
def health_check():
    """Check if N8N is accessible and responding"""
    try:
        # Try to connect to N8N's health endpoint
        response = requests.get(f"{N8N_BASE_URL}/healthz")
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'message': 'Connected to N8N successfully',
                'n8n_status': response.json()
            })
        else:
            return jsonify({
                'status': 'warning',
                'message': f'N8N responded with status code {response.status_code}',
                'details': response.text
            }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': 'Unable to connect to N8N',
            'error': str(e)
        }), 200  # Return 200 even for connection errors to allow clients to display the error

@workflow_bp.route('/workflows', methods=['GET'])
@jwt_required()
@admin_required
def get_workflows():
    """Get all workflows from N8N"""
    result = n8n_api_request('workflows')
    if result:
        return jsonify({
            'status': 'success',
            'data': result
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve workflows from N8N'
        }), 500

@workflow_bp.route('/workflows/<workflow_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_workflow(workflow_id):
    """Get a specific workflow by ID"""
    result = n8n_api_request(f'workflows/{workflow_id}')
    if result:
        return jsonify({
            'status': 'success',
            'data': result
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve workflow {workflow_id} from N8N'
        }), 404

@workflow_bp.route('/workflows', methods=['POST'])
@jwt_required()
@admin_required
def create_workflow():
    """Create a new workflow in N8N"""
    data = request.json
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No workflow data provided'
        }), 400
        
    result = n8n_api_request('workflows', method='POST', data=data)
    if result:
        return jsonify({
            'status': 'success',
            'message': 'Workflow created successfully',
            'data': result
        }), 201
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to create workflow in N8N'
        }), 500

@workflow_bp.route('/workflows/<workflow_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_workflow(workflow_id):
    """Update an existing workflow"""
    data = request.json
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No workflow data provided'
        }), 400
        
    result = n8n_api_request(f'workflows/{workflow_id}', method='PUT', data=data)
    if result:
        return jsonify({
            'status': 'success',
            'message': 'Workflow updated successfully',
            'data': result
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Failed to update workflow {workflow_id} in N8N'
        }), 500

@workflow_bp.route('/workflows/<workflow_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_workflow(workflow_id):
    """Delete a workflow"""
    result = n8n_api_request(f'workflows/{workflow_id}', method='DELETE')
    if result is not None:
        return jsonify({
            'status': 'success',
            'message': 'Workflow deleted successfully'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Failed to delete workflow {workflow_id} from N8N'
        }), 500

@workflow_bp.route('/workflows/<workflow_id>/activate', methods=['POST'])
@jwt_required()
@admin_required
def activate_workflow(workflow_id):
    """Activate a workflow (if it has a trigger)"""
    result = n8n_api_request(f'workflows/{workflow_id}/activate', method='POST')
    if result is not None:
        return jsonify({
            'status': 'success',
            'message': 'Workflow activated successfully',
            'data': result
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Failed to activate workflow {workflow_id}'
        }), 500

@workflow_bp.route('/workflows/<workflow_id>/deactivate', methods=['POST'])
@jwt_required()
@admin_required
def deactivate_workflow(workflow_id):
    """Deactivate a workflow"""
    result = n8n_api_request(f'workflows/{workflow_id}/deactivate', method='POST')
    if result is not None:
        return jsonify({
            'status': 'success',
            'message': 'Workflow deactivated successfully',
            'data': result
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Failed to deactivate workflow {workflow_id}'
        }), 500

@workflow_bp.route('/workflows/<workflow_id>/execute', methods=['POST'])
@jwt_required()
def execute_workflow(workflow_id):
    """Execute a workflow on demand"""
    data = request.json or {}
    
    # Add user identity to the workflow data
    user_id = get_jwt_identity()
    data['ecosyno_user_id'] = user_id
    
    result = n8n_api_request(f'workflows/{workflow_id}/execute', method='POST', data=data)
    if result:
        return jsonify({
            'status': 'success',
            'message': 'Workflow executed successfully',
            'data': result
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Failed to execute workflow {workflow_id}'
        }), 500

@workflow_bp.route('/webhooks/trigger', methods=['POST'])
def trigger_webhook():
    """Public endpoint to trigger workflows via webhooks"""
    # This endpoint allows external services to trigger N8N workflows
    # It can be secured with a webhook secret if needed
    
    data = request.json or {}
    webhook_id = request.args.get('id')
    
    if not webhook_id:
        return jsonify({
            'status': 'error',
            'message': 'Webhook ID is required'
        }), 400
    
    # Add timestamp to the data
    data['triggered_at'] = datetime.utcnow().isoformat()
    
    # Forward the request to N8N's webhook endpoint
    try:
        response = requests.post(
            f"{N8N_BASE_URL}/webhook/{webhook_id}",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code >= 200 and response.status_code < 300:
            try:
                return jsonify(response.json())
            except:
                return jsonify({
                    'status': 'success',
                    'message': 'Webhook triggered successfully'
                })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Webhook execution failed with status code {response.status_code}',
                'details': response.text
            }), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to forward webhook to N8N',
            'error': str(e)
        }), 500

# Admin Interface Routes

@workflow_bp.route('/admin/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def workflow_dashboard():
    """Get workflow statistics and status for admin dashboard"""
    workflows = n8n_api_request('workflows')
    executions = n8n_api_request('executions', params={'limit': 10})
    
    stats = {
        'total_workflows': len(workflows) if workflows else 0,
        'active_workflows': sum(1 for w in workflows if w.get('active', False)) if workflows else 0,
        'recent_executions': executions if executions else [],
        'status': 'connected' if workflows is not None else 'disconnected'
    }
    
    return jsonify({
        'status': 'success',
        'data': stats
    })

def register_n8n_workflow_module(app):
    """Register the N8N workflow manager blueprint with the Flask app"""
    app.register_blueprint(workflow_bp, url_prefix='/api/workflows')
    logger.info("N8N Workflow Manager registered successfully")
    return True