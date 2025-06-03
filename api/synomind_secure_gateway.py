"""
Secure SynoMind Gateway with Role-Based Access Control
Single SynoMind instance with intelligent role-based filtering and security
"""

import os
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from openai import OpenAI
from anthropic import Anthropic
from core.security_manager import security_manager

logger = logging.getLogger(__name__)

# Create secure SynoMind blueprint
synomind_secure_bp = Blueprint('synomind_secure', __name__, url_prefix='/api')

# Initialize AI clients
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
anthropic_client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

@synomind_secure_bp.route('/synomind-secure', methods=['POST'])
@jwt_required()
def synomind_secure_context():
    """
    Secure SynoMind endpoint with role-based access control
    Single AI instance that adapts responses based on user role
    """
    try:
        # Security validation
        security_report = security_manager.validate_request_security(
            endpoint=request.path,
            user_role=get_jwt().get('role', 'user')
        )
        
        if security_report['security_level'] == 'low':
            return jsonify({
                'status': 'error',
                'message': 'Security validation failed',
                'code': 'security_violation'
            }), 403
        
        # Get user info and role
        user_identity = get_jwt_identity()
        user_claims = get_jwt()
        user_role = user_claims.get('role', 'user')
        
        # Get role-specific SynoMind configuration
        synomind_config = security_manager.create_role_based_synomind_access(user_role)
        
        # Parse request data
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Invalid request: prompt is required'
            }), 400
        
        user_prompt = data['prompt']
        module = data.get('module', 'general')
        
        # Role-based prompt filtering and enhancement
        enhanced_prompt = _enhance_prompt_for_role(user_prompt, user_role, module, synomind_config)
        
        # Generate AI response with role-specific context
        ai_response = _generate_secure_ai_response(enhanced_prompt, synomind_config)
        
        # Filter response based on user role and permissions
        filtered_response = _filter_response_by_role(ai_response, user_role, synomind_config)
        
        # Log interaction for security audit
        _log_synomind_interaction(user_identity, user_role, user_prompt, module, security_report)
        
        return jsonify({
            'status': 'success',
            'response': filtered_response,
            'user_role': user_role,
            'access_level': synomind_config['access_level'],
            'security_level': security_report['security_level'],
            'audit_logged': True
        })
        
    except Exception as e:
        logger.error(f"Error in secure SynoMind endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred processing your request',
            'code': 'internal_error'
        }), 500

def _enhance_prompt_for_role(prompt: str, user_role: str, module: str, config: dict) -> str:
    """Enhance prompt based on user role and permissions"""
    
    role_context = {
        'super_admin': {
            'system_context': """You are SynoMind, the AI assistant for EcoSyno platform administrators. 
                               You have access to system-wide data and can provide insights about platform 
                               performance, user analytics, security monitoring, and technical recommendations.
                               You can discuss administrative functions, user management, and system optimization.""",
            'data_access': "You can access aggregated user data, system metrics, and platform analytics."
        },
        'admin': {
            'system_context': """You are SynoMind, the AI assistant for EcoSyno administrators. 
                               You can help with user management, content moderation, analytics review, 
                               and general administrative tasks. You cannot access individual user data 
                               or modify core system settings.""",
            'data_access': "You can access aggregated analytics and administrative functions only."
        },
        'user': {
            'system_context': """You are SynoMind, the personal AI assistant for EcoSyno users. 
                               You help with sustainable living, wellness tracking, eco-friendly recommendations, 
                               and personal goal achievement. You focus on the user's individual journey.""",
            'data_access': "You can only access the current user's personal data and preferences."
        }
    }
    
    context = role_context.get(user_role, role_context['user'])
    
    enhanced_prompt = f"""
{context['system_context']}

Current module: {module}
User role: {user_role}
Access level: {config['access_level']}
Data access: {context['data_access']}

User query: {prompt}

Respond appropriately based on the user's role and permissions. Always maintain security boundaries.
"""
    
    return enhanced_prompt

def _generate_secure_ai_response(prompt: str, config: dict) -> str:
    """Generate AI response using available models"""
    try:
        # Use OpenAI for most requests
        if openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are SynoMind, EcoSyno's intelligent assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        
        # Fallback to Anthropic
        elif anthropic_client:
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        
        else:
            return "I'm currently unable to process your request. Please ensure AI services are properly configured."
    
    except Exception as e:
        logger.error(f"AI response generation error: {str(e)}")
        return "I encountered an issue processing your request. Please try again later."

def _filter_response_by_role(response: str, user_role: str, config: dict) -> str:
    """Filter AI response based on user role and permissions"""
    
    # Super admins get full response
    if user_role == 'super_admin':
        return response
    
    # Filter sensitive information for admin users
    if user_role == 'admin':
        # Remove any specific user data references
        filtered_response = response
        sensitive_patterns = [
            r'user ID \d+',
            r'email: [^\s]+@[^\s]+',
            r'phone: [^\s]+',
            r'address: [^\n]+'
        ]
        
        import re
        for pattern in sensitive_patterns:
            filtered_response = re.sub(pattern, '[REDACTED]', filtered_response, flags=re.IGNORECASE)
        
        return filtered_response
    
    # Regular users get standard response with personal context
    return response + "\n\n*This response is personalized for your EcoSyno journey.*"

def _log_synomind_interaction(user_id: str, user_role: str, prompt: str, module: str, security_report: dict):
    """Log SynoMind interaction for security and audit purposes"""
    try:
        from datetime import datetime
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'user_role': user_role,
            'module': module,
            'prompt_length': len(prompt),
            'security_level': security_report['security_level'],
            'endpoint': '/api/synomind-secure',
            'interaction_type': 'ai_query'
        }
        
        # In production, this would go to a secure audit log
        logger.info(f"SynoMind interaction logged: {log_entry}")
        
    except Exception as e:
        logger.error(f"Failed to log SynoMind interaction: {str(e)}")

# Additional endpoint for testing role-based access
@synomind_secure_bp.route('/synomind-test-access', methods=['GET'])
@jwt_required()
def test_synomind_access():
    """Test endpoint to verify role-based SynoMind access"""
    user_role = get_jwt().get('role', 'user')
    config = security_manager.create_role_based_synomind_access(user_role)
    
    return jsonify({
        'user_role': user_role,
        'synomind_config': config,
        'message': f'SynoMind access configured for {user_role} role'
    })