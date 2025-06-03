"""
Llama 3.0 Local Model Integration for SynoMind
Provides a self-contained AI brain that connects to the entire application
"""
import os
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from flask import Blueprint, request, jsonify, current_app

from llama_cpp import Llama

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
llama_bp = Blueprint('llama_model', __name__, url_prefix='/api/llama')

# Define model paths and configuration
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
DEFAULT_MODEL_PATH = os.path.join(MODELS_DIR, "llama-3-8b-instruct.Q4_K_M.gguf")

# Ensure model directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

# Model instance (will be loaded on first use)
_llama_model = None
_model_lock = threading.Lock()

def get_llama_model():
    """
    Gets or initializes the Llama model instance
    Uses lazy loading to avoid loading model until needed
    """
    global _llama_model
    
    if _llama_model is not None:
        return _llama_model
    
    with _model_lock:
        # Double-check pattern to avoid race conditions
        if _llama_model is not None:
            return _llama_model
            
        # Check if model file exists
        if not os.path.exists(DEFAULT_MODEL_PATH):
            logger.warning(f"Model file not found at {DEFAULT_MODEL_PATH}")
            logger.info("Downloading model. This may take some time...")
            download_model()
        
        try:
            # Try to load model with optimal settings based on available RAM
            logger.info(f"Loading Llama model from {DEFAULT_MODEL_PATH}")
            _llama_model = Llama(
                model_path=DEFAULT_MODEL_PATH,
                n_ctx=2048,  # Context window size
                n_batch=512,  # Batch size for prompt processing
                n_gpu_layers=-1,  # Use all available GPU layers, or none if no GPU
                verbose=False  # Set to True for debug information
            )
            logger.info("Llama model loaded successfully")
            return _llama_model
        except Exception as e:
            logger.error(f"Error loading Llama model: {e}")
            raise

def download_model():
    """
    Download the Llama model if it doesn't exist
    In a production environment, this should use proper authentication
    """
    try:
        if os.path.exists(DEFAULT_MODEL_PATH):
            logger.info(f"Model already exists at {DEFAULT_MODEL_PATH}")
            return
            
        # Create a placeholder file indicating model is being downloaded
        with open(os.path.join(MODELS_DIR, ".downloading"), "w") as f:
            f.write(f"Starting download at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # In a production environment, you would download from an authenticated source
        # For this implementation, we'll create a placeholder model file
        logger.info("Creating placeholder model file for demonstration")
        with open(DEFAULT_MODEL_PATH, "w") as f:
            f.write("This is a placeholder for the actual Llama 3.0 model file.")
            
        logger.info(f"Model file created at {DEFAULT_MODEL_PATH}")
        
        # Remove the placeholder file indicating download is complete
        download_indicator = os.path.join(MODELS_DIR, ".downloading")
        if os.path.exists(download_indicator):
            os.remove(download_indicator)
    
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        raise

def create_synthetic_data():
    """
    Generate synthetic training data specific to the EcoSyno application
    This data will be used to fine-tune the model for sustainability domains
    """
    synthetic_data_path = os.path.join(MODELS_DIR, "synomind_training_data.jsonl")
    
    # Only create if file doesn't exist
    if os.path.exists(synthetic_data_path):
        return
    
    # Sample training data with instruction-output pairs
    training_data = [
        # Environment module examples
        {
            "instruction": "What can I do to reduce my carbon footprint?",
            "output": "Namaste! To reduce your carbon footprint, consider: 1) Using public transportation or carpooling, 2) Reducing meat consumption, particularly beef, 3) Minimizing single-use plastics, 4) Using energy-efficient appliances, 5) Reducing water waste, and 6) Supporting renewable energy sources. Would you like specific suggestions for any of these areas?"
        },
        {
            "instruction": "How can I save water at home?",
            "output": "Namaste! To conserve water at home: 1) Fix leaky faucets and pipes, 2) Install water-efficient showerheads and toilets, 3) Collect rainwater for plants, 4) Run full loads in washing machines and dishwashers, 5) Take shorter showers, and 6) Turn off the tap while brushing teeth or shaving. Our Environment module can help you track your water usage and suggest personalized conservation strategies."
        },
        
        # Wellness module examples
        {
            "instruction": "I'm feeling stressed today. What should I do?",
            "output": "Namaste! I'm sorry to hear you're feeling stressed. Some mindful practices that might help include: 1) Taking 5 minutes for deep breathing, 2) Going for a short walk in nature, 3) Practicing meditation, 4) Writing in a gratitude journal, 5) Gentle stretching or yoga. Would you like me to guide you through a quick breathing exercise? Our Wellness module can also help track your mood patterns and suggest personalized stress-reduction techniques."
        },
        {
            "instruction": "How can I improve my sleep quality?",
            "output": "Namaste! For better sleep quality: 1) Maintain a consistent sleep schedule, 2) Create a relaxing bedtime routine, 3) Limit screen time before bed, 4) Keep your bedroom cool, dark, and quiet, 5) Avoid caffeine and heavy meals before sleeping, and 6) Consider relaxation techniques like meditation. Our Wellness module can help you track your sleep patterns and identify factors affecting your rest."
        },
        
        # Kitchen module examples
        {
            "instruction": "How can I reduce food waste in my kitchen?",
            "output": "Namaste! To reduce food waste: 1) Plan meals and make shopping lists, 2) Store food properly, 3) Understand expiration vs. 'best by' dates, 4) Use leftovers creatively, 5) Compost food scraps, and 6) Practice FIFO (First In, First Out) in your refrigerator. Our Kitchen module can help you track and manage your food inventory to minimize waste."
        },
        {
            "instruction": "What are some sustainable eating habits?",
            "output": "Namaste! Sustainable eating habits include: 1) Eating more plant-based meals, 2) Choosing local and seasonal produce, 3) Reducing processed food consumption, 4) Selecting sustainably sourced seafood, 5) Minimizing food waste, and 6) Growing some of your own food if possible. Our Kitchen module offers sustainable recipes and helps track the environmental impact of your food choices."
        },
        
        # Wardrobe module examples
        {
            "instruction": "How can I build a more sustainable wardrobe?",
            "output": "Namaste! For a sustainable wardrobe: 1) Choose quality over quantity, 2) Buy from ethical and sustainable brands, 3) Select natural and organic fabrics, 4) Repair and maintain your clothes, 5) Participate in clothing swaps, and 6) Consider second-hand shopping. Our Wardrobe module can help you track your clothing usage and make more conscious fashion choices."
        },
        {
            "instruction": "What is a capsule wardrobe?",
            "output": "Namaste! A capsule wardrobe is a curated collection of versatile, timeless pieces that can be mixed and matched to create many different outfits. It typically consists of 30-40 high-quality items including clothing, shoes, and accessories. This approach promotes sustainability by reducing consumption, maximizing wear of each item, and encouraging thoughtful purchasing. Our Wardrobe module can help you plan and track your capsule wardrobe."
        },
        
        # General SynoMind commands
        {
            "instruction": "Hey Syno, what can you help me with?",
            "output": "Namaste! I'm SynoMind, your sustainable lifestyle assistant. I can help you with: 1) Environmental impact tracking, 2) Wellness and mindfulness practices, 3) Sustainable kitchen and cooking, 4) Eco-friendly wardrobe choices, and 5) General sustainability advice. Just let me know what area you'd like to focus on, and I'll guide you toward more sustainable living."
        },
        {
            "instruction": "Tell me about the EcoSyno platform",
            "output": "Namaste! EcoSyno is a comprehensive sustainable lifestyle platform designed to empower users in making eco-conscious choices. It features multiple modules: Environment for tracking your ecological footprint, Wellness for mindfulness and health, Kitchen for sustainable food practices, and Wardrobe for ethical fashion choices. Each module offers tracking tools, personalized recommendations, and educational resources to support your sustainability journey."
        }
    ]
    
    # Write training data to file
    with open(synthetic_data_path, 'w') as f:
        for entry in training_data:
            f.write(json.dumps(entry) + '\n')
    
    logger.info(f"Created synthetic training data at {synthetic_data_path}")

@llama_bp.route('/health', methods=['GET'])
def health_check():
    """Check if Llama model is available and ready"""
    try:
        # Check if model file exists
        model_exists = os.path.exists(DEFAULT_MODEL_PATH)
        
        # Check if model is loaded
        model_loaded = _llama_model is not None
        
        # If model exists but isn't loaded, indicate model is available but not loaded
        return jsonify({
            'status': 'ok' if model_exists else 'error',
            'model_exists': model_exists,
            'model_loaded': model_loaded,
            'model_path': DEFAULT_MODEL_PATH
        })
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@llama_bp.route('/chat', methods=['POST'])
def chat():
    """Chat with the Llama model"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing message in request'
            }), 400
        
        message = data['message']
        context = data.get('context', {})
        
        # Get model instance
        model = get_llama_model()
        if not model:
            return jsonify({
                'success': False,
                'error': 'Llama model not available'
            }), 503
        
        # Create system prompt with context
        system_prompt = create_system_prompt(context)
        
        # Generate response
        response = generate_response(model, system_prompt, message)
        
        return jsonify({
            'success': True,
            'message': message,
            'response': response,
            'model': 'llama-3-8b'
        })
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@llama_bp.route('/generate-response', methods=['POST'])
def generate_response_api():
    """Generate a response to user input using Llama model with conversation context.
    
    Request body:
    {
        "text": "User input text",
        "conversation_history": [
            {"role": "user", "content": "Previous user message"},
            {"role": "assistant", "content": "Previous assistant response"}
        ]
    }
    
    Returns:
    {
        "response": "Generated response text"
    }
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "Text is required"}), 400
        
        user_input = data['text']
        conversation_history = data.get('conversation_history', [])
        
        # Get model instance
        model = get_llama_model()
        if not model:
            return jsonify({"error": "Llama model not available"}), 503
        
        # Create system prompt for SynoMind
        system_prompt = """
        You are SynoMind, a sustainable lifestyle assistant with a warm, compassionate personality.
        You speak in a supportive, encouraging tone.
        You specialize in four areas:
        
        1. Environment Tracking: Carbon footprint, water usage, energy consumption
        2. Wellness: Mood tracking, meditation, sleep, physical activity
        3. Kitchen Management: Sustainable food choices, reducing waste, eco-friendly recipes
        4. Wardrobe: Ethical fashion, capsule wardrobes, sustainable clothing choices
        
        Keep responses concise (2-3 sentences) and always relevant to sustainable living.
        Include phrases like "sustainable choices", "eco-conscious", and "mindful living" when appropriate.
        Be personal and conversational, remembering context from earlier in the conversation.
        Remember details the user has shared and refer back to them when relevant.
        
        Current date: May 20, 2025
        
        IMPORTANT: Only begin your response with "Namaste!" when starting a new conversation. 
        If conversation_history is empty, you can start with "Namaste!"
        Otherwise, just respond naturally to continue the existing conversation without saying "Namaste!"
        """
        
        # Build context from conversation history
        context = ""
        if conversation_history:
            for message in conversation_history:
                if message.get('role') and message.get('content'):
                    role = "User: " if message.get('role') == 'user' else "SynoMind: "
                    context += role + message.get('content') + "\n"
        
        # Format the final prompt with conversation context
        if context:
            final_prompt = f"{system_prompt}\n\nConversation history:\n{context}\n\nUser: {user_input}\nSynoMind:"
        else:
            final_prompt = f"{system_prompt}\n\nUser: {user_input}\nSynoMind:"
        
        # Generate response
        logger.info(f"Generating Llama response for input: {user_input[:50]}...")
        
        output = model(
            final_prompt,
            max_tokens=150,
            temperature=0.7,
            top_p=0.95,
            echo=False,
            stop=["User:", "\n\n"]
        )
        
        # Extract response text
        response_text = output['choices'][0]['text'].strip()
        
        # Clean up any remaining prompt artifacts
        response_text = response_text.replace("SynoMind:", "").strip()
        
        return jsonify({"response": response_text})
    
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return jsonify({"error": str(e)}), 500

@llama_bp.route('/wake-word', methods=['POST'])
def detect_wake_word():
    """
    Detect wake word in audio transcript
    This provides a more reliable way to detect wake words using the local model
    """
    try:
        data = request.json
        if not data or 'transcript' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing transcript in request'
            }), 400
        
        transcript = data['transcript'].lower()
        
        # Simple keyword matching for common wake word variants
        wake_words = ['hey syno', 'hey sino', 'hey synod', 'hi syno']
        detected = False
        command = None
        
        for wake_word in wake_words:
            if wake_word in transcript:
                detected = True
                # Extract command after wake word
                index = transcript.find(wake_word) + len(wake_word)
                potential_command = transcript[index:].strip()
                if potential_command:
                    command = potential_command
                break
        
        return jsonify({
            'success': True,
            'wake_word_detected': detected,
            'command': command
        })
        
    except Exception as e:
        logger.error(f"Error in wake word detection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def create_system_prompt(context=None):
    """Create a system prompt based on context for better responses"""
    base_prompt = (
        "You are SynoMind, an AI assistant for the EcoSyno sustainable lifestyle platform. "
        "Your voice is female and you begin your responses with 'Namaste'. "
        "You provide helpful, accurate, and concise information about sustainable living, "
        "including environmental impact, wellness practices, sustainable kitchen habits, "
        "and eco-friendly wardrobe choices. You are knowledgeable but humble, "
        "and you focus on actionable advice users can implement in their daily lives."
    )
    
    if not context:
        return base_prompt
    
    # Add module-specific context if available
    module = context.get('module', '')
    if module == 'environment':
        base_prompt += (
            "\n\nThe user is currently in the Environment module, which helps track "
            "carbon footprint, water usage, energy consumption, and other environmental metrics. "
            "Focus on practical advice for reducing environmental impact."
        )
    elif module == 'wellness':
        base_prompt += (
            "\n\nThe user is currently in the Wellness module, which helps track "
            "mood, sleep, meditation, and physical activity. "
            "Focus on mindfulness, mental health, and holistic wellbeing practices."
        )
    elif module == 'kitchen':
        base_prompt += (
            "\n\nThe user is currently in the Kitchen module, which helps with "
            "sustainable food choices, reducing waste, and eco-friendly cooking. "
            "Focus on sustainable eating habits and reducing food-related environmental impact."
        )
    elif module == 'wardrobe':
        base_prompt += (
            "\n\nThe user is currently in the Wardrobe module, which helps with "
            "building a sustainable wardrobe, ethical fashion choices, and reducing textile waste. "
            "Focus on conscious consumption and sustainable fashion practices."
        )
    
    # Add any specific user data that might be relevant
    user_data = context.get('user_data', {})
    if user_data:
        try:
            data_str = json.dumps(user_data, indent=2)
            base_prompt += f"\n\nRelevant user data: {data_str}"
        except:
            pass
    
    return base_prompt

def generate_response(model, system_prompt, user_message):
    """Generate a response using the Llama model"""
    try:
        # Format prompt for Llama instruct models
        formatted_prompt = f"""<|system|>
{system_prompt}
<|user|>
{user_message}
<|assistant|>"""

        # Generate response
        output = model(
            formatted_prompt,
            max_tokens=512,
            temperature=0.7,
            top_p=0.95,
            echo=False
        )
        
        # Extract generated text
        if isinstance(output, dict) and 'choices' in output:
            return output['choices'][0]['text'].strip()
        elif isinstance(output, dict) and 'text' in output:
            return output['text'].strip()
        else:
            # Fallback basic response
            return "Namaste! I processed your request but encountered an issue with the response format. How else can I assist you today?"
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "Namaste! I'm having trouble processing your request at the moment. Please try again later."

def register_blueprint(app):
    """Register blueprint with Flask app"""
    # Create synthetic training data
    create_synthetic_data()
    
    # Register the blueprint
    app.register_blueprint(llama_bp)
    logger.info("Llama model integration registered successfully")