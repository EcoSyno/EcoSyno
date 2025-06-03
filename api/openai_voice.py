"""OpenAI Voice API integration for SynoMind.

This module provides API endpoints for text-to-speech and speech-to-text
conversion using OpenAI's premium voice and speech recognition capabilities.
"""

import os
import tempfile
import base64
from flask import Blueprint, request, jsonify
import requests
from openai import OpenAI

# Initialize blueprint
openai_voice_bp = Blueprint('openai_voice', __name__, url_prefix='/api/openai')

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
DEFAULT_MODEL = "gpt-4o"

@openai_voice_bp.route('/health', methods=['GET'])
def health_check():
    """Check if OpenAI service is available."""
    try:
        # Simple health check by creating a small completion
        client.chat.completions.create(
            model=DEFAULT_MODEL, 
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=5
        )
        return jsonify({"status": "ok", "message": "OpenAI service is available"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@openai_voice_bp.route('/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech using OpenAI's TTS API.
    
    Request body:
    {
        "text": "Text to convert to speech",
        "voice": "alloy" | "echo" | "fable" | "onyx" | "nova" | "shimmer"
    }
    
    Returns:
    {
        "audio": "base64 encoded audio data"
    }
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "Text is required"}), 400
        
        text = data['text']
        voice = data.get('voice', 'nova')  # Default to nova (female voice)
        
        # Validate voice
        valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice not in valid_voices:
            return jsonify({"error": f"Invalid voice. Choose from: {', '.join(valid_voices)}"}), 400
        
        # Generate speech
        print(f"Generating speech for: {text[:30]}... with voice: {voice}")
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save to temporary file and read back as bytes
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            response.stream_to_file(tmp.name)
            tmp.flush()
            tmp.seek(0)
            audio_data = tmp.read()
        
        # Convert to base64 for transmission
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return jsonify({"audio": audio_base64})
    
    except Exception as e:
        print(f"Error in TTS: {str(e)}")
        return jsonify({"error": str(e)}), 500

@openai_voice_bp.route('/stt', methods=['POST'])
def speech_to_text():
    """Convert speech to text using OpenAI's Whisper API.
    
    Request body should be multipart/form-data with an 'audio' file.
    
    Returns:
    {
        "text": "Transcribed text"
    }
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "Audio file is required"}), 400
        
        audio_file = request.files['audio']
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            audio_file.save(tmp.name)
            tmp.flush()
            
            # Transcribe
            with open(tmp.name, "rb") as file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=file
                )
        
        return jsonify({"text": transcript.text})
    
    except Exception as e:
        print(f"Error in STT: {str(e)}")
        return jsonify({"error": str(e)}), 500

@openai_voice_bp.route('/generate-response', methods=['POST'])
def generate_response():
    """Generate a response to user input using OpenAI's chat API with conversation context.
    
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
        
        # Default system message for SynoMind
        system_message = """
        You are SynoMind, a sustainable lifestyle assistant with a warm, compassionate personality.
        You always greet users with "Namaste" and speak in a supportive, encouraging tone.
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
        """
        
        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history
        for message in conversation_history:
            if message.get('role') in ['user', 'assistant'] and message.get('content'):
                messages.append(message)
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        print(f"Sending {len(messages)} messages to OpenAI, including system message")
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            max_tokens=150,  # Keep responses concise
            temperature=0.7  # Slightly creative but mostly consistent
        )
        
        response_text = response.choices[0].message.content
        
        return jsonify({"response": response_text})
    
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return jsonify({"error": str(e)}), 500


def register_openai_voice(app):
    """Register the OpenAI voice blueprint with the Flask app."""
    app.register_blueprint(openai_voice_bp)
    print("OpenAI voice integration registered successfully")
    return openai_voice_bp