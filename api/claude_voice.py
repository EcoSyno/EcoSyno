"""
Claude Voice API for SynoMind
Provides API endpoints for dynamic responses using Anthropic's Claude model.
"""

import os
import tempfile
import base64
import json
from flask import Blueprint, request, jsonify
import anthropic

# Initialize blueprint
claude_voice_bp = Blueprint('claude_voice', __name__, url_prefix='/api/claude')

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

@claude_voice_bp.route('/health', methods=['GET'])
def health_check():
    """Check if Anthropic service is available."""
    try:
        # Simple health check using a small message
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        return jsonify({"status": "ok", "message": "Anthropic Claude service is available"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@claude_voice_bp.route('/generate-response', methods=['POST'])
def generate_response():
    """Generate a response to user input using Anthropic Claude API.
    
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
        
        # System message for SynoMind
        system_message = """
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
        
        # Build messages for Claude
        messages = []
        
        # Add conversation history
        for message in conversation_history:
            if message.get('role') in ['user', 'assistant'] and message.get('content'):
                role = message.get('role')
                # Anthropic uses 'assistant' but we need to adapt from OpenAI format
                messages.append({
                    "role": role,
                    "content": message.get('content')
                })
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        print(f"Sending request to Claude with {len(messages)} messages")
        
        # Get response from Claude
        response = client.messages.create(
            model=DEFAULT_MODEL,
            system=system_message,
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        
        # Access the Claude API response and extract text safely
        try:
            # For Claude 3.5, we need to extract text content properly
            response_text = ""
            
            # Claude 3.5 content format has an array of content blocks
            if hasattr(response, 'content') and response.content:
                for content_block in response.content:
                    # Check if it's a text block
                    if hasattr(content_block, 'type') and content_block.type == 'text':
                        response_text += content_block.text
                    # For other content types like images, we'd handle differently
            
            # If we didn't extract any text this way, try the direct text attribute
            if not response_text and hasattr(response, 'text'):
                response_text = response.text
                
            # Final fallback: convert to string representation
            if not response_text:
                print("Using string representation fallback for Claude response")
                # Only get the text after analyzing the structure
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else {}
                content = response_dict.get('content', [])
                
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        response_text += item.get('text', '')
                
            # Clean up the response if needed
            if not response_text and hasattr(response, 'content'):
                # Last resort: direct string access to first content item
                try:
                    response_text = response.content[0].text
                except:
                    # If all else fails, use a direct string representation
                    response_text = str(response)
                    
            # Log successful extraction
            print(f"Extracted Claude response: {response_text[:50]}...")
                    
        except Exception as e:
            print(f"Error extracting Claude response: {e}")
            # Fall back to using a simple string conversion of the whole response
            try:
                response_text = str(response)
            except:
                response_text = "I couldn't generate a proper response due to a technical issue."
                
        # If all extraction methods failed
        if not response_text:
            response_text = "I'm sorry, I couldn't generate a proper response."
        
        return jsonify({"response": response_text})
    
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return jsonify({"error": str(e)}), 500


def register_claude_voice(app):
    """Register the Claude voice blueprint with the Flask app."""
    app.register_blueprint(claude_voice_bp)
    print("Claude voice integration registered successfully")
    return claude_voice_bp