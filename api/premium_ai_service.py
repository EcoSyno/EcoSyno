"""
Premium AI Service API
Provides endpoints for premium AI processing with OpenAI and Anthropic Claude models
"""
import os
import json
import logging
from flask import Blueprint, request, jsonify
import openai
import anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
premium_ai_bp = Blueprint('premium_ai', __name__, url_prefix='/api/premium-ai')

# Initialize API variables
openai_api_key = os.environ.get('OPENAI_API_KEY')
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
openai_client = None
anthropic_client = None
AI_SERVICES_AVAILABLE = False

# Initialize API clients
try:
    # Initialize OpenAI client
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    if openai_api_key:
        openai_client = openai.OpenAI(api_key=openai_api_key)
    
    # Initialize Anthropic client
    # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
    if anthropic_api_key:
        anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    # Check if at least one service is available
    if openai_client or anthropic_client:
        AI_SERVICES_AVAILABLE = True
        logger.info("Premium AI services initialized successfully")
except Exception as e:
    AI_SERVICES_AVAILABLE = False
    logger.error(f"Error initializing premium AI services: {e}")

@premium_ai_bp.route('/health', methods=['GET'])
def health_check():
    """Check if premium AI services are available"""
    if AI_SERVICES_AVAILABLE:
        return jsonify({
            'status': 'ok',
            'services': {
                'openai': openai_api_key is not None,
                'anthropic': anthropic_api_key is not None
            }
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Premium AI services are not available'
        }), 503

@premium_ai_bp.route('/process-text', methods=['POST'])
def process_text():
    """Process text commands with premium AI"""
    if not AI_SERVICES_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Premium AI services are not available'
        }), 503
    
    data = request.json
    if not data or 'text' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing text in request'
        }), 400
    
    text = data['text']
    context = data.get('context', {})
    
    try:
        # Decide which AI service to use based on the task
        result = process_with_best_model(text, context)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing text with premium AI: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@premium_ai_bp.route('/process-voice', methods=['POST'])
def process_voice():
    """Process voice audio with premium AI"""
    if not AI_SERVICES_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Premium AI services are not available'
        }), 503
    
    data = request.json
    if not data or 'audio_data' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing audio_data in request'
        }), 400
    
    # In a real implementation, we would process the audio data here
    # For now, we'll just return a dummy response
    return jsonify({
        'success': True,
        'response': 'I processed your voice command, but voice transcription is not yet implemented.',
        'actions': []
    })

def process_with_best_model(text, context=None):
    """Process text with the most appropriate AI model"""
    # Determine which model to use based on the task
    task_type = determine_task_type(text)
    
    if task_type == 'visual':
        # For visual tasks, use OpenAI GPT-4o with vision capabilities
        return process_with_openai(text, context, include_vision=True)
    elif task_type == 'complex':
        # For complex reasoning tasks, use Anthropic Claude
        return process_with_claude(text, context)
    else:
        # For most general tasks, use GPT-4o
        return process_with_openai(text, context)

def determine_task_type(text):
    """
    Determine the type of task based on the text
    Returns one of: 'general', 'visual', 'complex'
    """
    text_lower = text.lower()
    
    # Visual task indicators
    visual_keywords = [
        'image', 'picture', 'photo', 'see', 'camera', 
        'look at', 'analyze this', 'what is in', 'scan'
    ]
    
    # Complex reasoning task indicators
    complex_keywords = [
        'explain', 'analyze', 'compare', 'evaluate', 'critique',
        'why is', 'how would', 'what if', 'implications', 'synthesize'
    ]
    
    for keyword in visual_keywords:
        if keyword in text_lower:
            return 'visual'
    
    for keyword in complex_keywords:
        if keyword in text_lower:
            return 'complex'
    
    return 'general'

def process_with_openai(text, context=None, include_vision=False):
    """Process text with OpenAI's GPT-4o"""
    try:
        # Check if OpenAI client is available
        if not openai_client:
            return {
                'success': False,
                'error': 'OpenAI client is not available',
                'response': 'Namaste! I am having trouble connecting to my AI services. Please try again later or contact support.',
                'actions': []
            }
            
        # Create system message with context
        system_message = create_system_message(context)
        
        # Create the messages array
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": text}
        ]
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract response content
        response_text = response.choices[0].message.content
        
        # Parse any actions from the response
        actions = extract_actions(response_text)
        
        return {
            'success': True,
            'response': response_text,
            'actions': actions
        }
    except Exception as e:
        logger.error(f"Error in process_with_openai: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def process_with_claude(text, context=None):
    """Process text with Anthropic's Claude"""
    try:
        # Create system message with context
        system_message = create_system_message(context)
        
        # Call Anthropic API
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=system_message,
            messages=[
                {"role": "user", "content": text}
            ]
        )
        
        # Extract response content - safely handle different response formats
        response_text = ""
        if hasattr(response, 'content') and response.content:
            if isinstance(response.content, list) and len(response.content) > 0:
                if hasattr(response.content[0], 'text'):
                    response_text = response.content[0].text
                else:
                    # Try to extract as dictionary
                    content_item = response.content[0]
                    if isinstance(content_item, dict) and 'text' in content_item:
                        response_text = content_item['text']
            elif isinstance(response.content, dict) and 'text' in response.content:
                response_text = response.content['text']
        
        # If we couldn't extract text, provide a fallback response
        if not response_text:
            response_text = "Namaste! I processed your request but had difficulty with the response format. How else can I assist you today?"
        
        # Parse any actions from the response
        actions = extract_actions(response_text)
        
        return {
            'success': True,
            'response': response_text,
            'actions': actions
        }
    except Exception as e:
        logger.error(f"Error in process_with_claude: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def create_system_message(context=None):
    """Create a system message with context information"""
    if not context:
        return "You are SynoMind, an AI assistant focused on sustainable lifestyle. Your voice is female and you start your responses with 'Namaste'. Be concise, helpful, and provide actionable advice related to environmental consciousness, wellness, sustainable kitchen practices, and eco-friendly wardrobe choices."
    
    # Extract context information
    module = context.get('module', 'dashboard')
    module_context = context.get('context', {})
    
    # Base system message
    base_message = "You are SynoMind, an AI assistant focused on sustainable lifestyle. Your voice is female and you start your responses with 'Namaste'. Be concise, helpful, and provide actionable advice."
    
    # Add module-specific context
    if module == 'environment':
        base_message += " The user is currently in the Environment module, which tracks eco-friendly actions, carbon footprint, water usage, and energy consumption."
    elif module == 'wellness':
        base_message += " The user is currently in the Wellness module, which focuses on physical and mental wellbeing, mood tracking, sleep quality, meditation, and exercise."
    elif module == 'kitchen':
        base_message += " The user is currently in the Kitchen module, which helps with sustainable food choices, reducing waste, meal planning, and eco-friendly cooking practices."
    elif module == 'wardrobe':
        base_message += " The user is currently in the Wardrobe module, which assists with building a sustainable and ethical wardrobe, tracking clothing usage, and minimizing fashion waste."
    
    # Add any specific module context data
    if module_context:
        try:
            context_str = json.dumps(module_context, indent=2)
            base_message += f"\n\nCurrent context data: {context_str}"
        except:
            pass
    
    return base_message

def extract_actions(response_text):
    """
    Extract any special actions from the response text
    Actions should be in a format like [ACTION:navigate:/app/environment]
    """
    actions = []
    
    # Simple action extraction using brackets
    import re
    action_pattern = r'\[ACTION:(.*?)\]'
    action_matches = re.findall(action_pattern, response_text)
    
    for action_str in action_matches:
        parts = action_str.split(':')
        if len(parts) >= 2:
            action_type = parts[0].strip()
            action_value = parts[1].strip()
            
            actions.append({
                'type': action_type,
                'target': action_value
            })
    
    return actions

def register_blueprint(app):
    """Register blueprint with Flask app"""
    app.register_blueprint(premium_ai_bp)
    logger.info("Premium AI service registered successfully")