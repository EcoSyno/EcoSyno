"""
Google AI Training Integration for SynoMind
Real Gemini API integration with voice and multi-language support
"""
import os
import logging
from flask import Blueprint, request, jsonify
import time
import json

logger = logging.getLogger(__name__)

# Configure Google AI with your API key
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

try:
    import google.generativeai as genai
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        logger.info("Google AI configured successfully with API key")
    else:
        logger.warning("Google API key not found in environment")
except ImportError:
    logger.error("Google Generative AI library not available")
    genai = None

google_ai_bp = Blueprint('google_ai_training', __name__)

class GoogleAITrainingService:
    def __init__(self):
        self.models = {
            'gemini-1.5-pro': 'gemini-1.5-pro-latest',
            'gemini-1.5-flash': 'gemini-1.5-flash-latest', 
            'gemini-1.0-pro': 'gemini-1.0-pro-latest'
        }
        self.training_sessions = {}
        
    def is_configured(self):
        """Check if Google AI is properly configured"""
        return bool(GOOGLE_API_KEY) and bool(genai)
    
    def start_voice_training(self, config):
        """Start voice training with Gemini AI"""
        try:
            if not self.is_configured():
                return {'success': False, 'error': 'Google AI not configured'}
            
            model_name = config.get('model', 'gemini-1.5-pro')
            languages = config.get('languages', ['en'])
            voices = config.get('voices', {})
            
            # Create training session
            session_id = f"gemini_training_{int(time.time())}"
            
            # Initialize Gemini model
            model = genai.GenerativeModel(self.models.get(model_name, 'gemini-1.5-pro-latest'))
            
            # Create training prompts for each language
            training_prompts = self._create_multilingual_prompts(languages, voices)
            
            # Store training session
            self.training_sessions[session_id] = {
                'model': model_name,
                'languages': languages,
                'voices': voices,
                'prompts': training_prompts,
                'status': 'running',
                'progress': 0,
                'start_time': time.time(),
                'results': []
            }
            
            return {
                'success': True,
                'session_id': session_id,
                'model': model_name,
                'languages': languages,
                'total_prompts': len(training_prompts)
            }
            
        except Exception as e:
            logger.error(f"Error starting Gemini training: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_multilingual_prompts(self, languages, voices):
        """Create training prompts for multiple languages"""
        prompts = []
        
        base_prompts = {
            'en': [
                "You are SynoMind, an eco-friendly AI assistant. Help users with sustainable living choices.",
                "Provide eco-friendly alternatives for daily activities and products.",
                "Guide users in reducing their carbon footprint through practical advice."
            ],
            'hi': [
                "आप SynoMind हैं, एक पर्यावरण-अनुकूल AI सहायक। उपयोगकर्ताओं को टिकाऊ जीवनशैली विकल्पों में मदद करें।",
                "दैनिक गतिविधियों और उत्पादों के लिए पर्यावरण-अनुकूल विकल्प प्रदान करें।",
                "व्यावहारिक सलाह के माध्यम से उपयोगकर्ताओं को अपने कार्बन फुटप्रिंट को कम करने में मार्गदर्शन करें।"
            ],
            'te': [
                "మీరు SynoMind, పర్యావరణ అనుకూల AI సహాయకుడు. వినియోగదారులకు స్థిరమైన జీవన ఎంపికలలో సహాయం చేయండి.",
                "రోజువారీ కార్యకలాపాలు మరియు ఉత్పత్తులకు పర్యావరణ అనుకూల ప్రత్యామ్నాయాలను అందించండి।",
                "ఆచరణాత్మక సలహా ద్వారా వినియోగదారులను వారి కార్బన్ పాదముద్రను తగ్గించడంలో మార్గనిర్దేశం చేయండి."
            ]
        }
        
        for lang in languages:
            if lang in base_prompts:
                for i, prompt in enumerate(base_prompts[lang]):
                    voice_config = voices.get(lang, 'neutral')
                    prompts.append({
                        'language': lang,
                        'voice': voice_config,
                        'prompt': prompt,
                        'index': i
                    })
        
        return prompts
    
    def process_training_batch(self, session_id, batch_size=3):
        """Process a batch of training prompts"""
        try:
            session = self.training_sessions.get(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            model = genai.GenerativeModel(self.models.get(session['model'], 'gemini-1.5-pro-latest'))
            prompts = session['prompts']
            current_progress = session['progress']
            
            # Process next batch
            start_idx = int(current_progress * len(prompts) / 100)
            end_idx = min(start_idx + batch_size, len(prompts))
            
            batch_results = []
            for i in range(start_idx, end_idx):
                prompt_data = prompts[i]
                
                try:
                    # Generate response with Gemini
                    response = model.generate_content(
                        f"Training prompt for {prompt_data['language']} voice assistant: {prompt_data['prompt']}"
                    )
                    
                    batch_results.append({
                        'prompt_index': i,
                        'language': prompt_data['language'],
                        'voice': prompt_data['voice'],
                        'response': response.text,
                        'success': True
                    })
                    
                except Exception as e:
                    batch_results.append({
                        'prompt_index': i,
                        'language': prompt_data['language'],
                        'error': str(e),
                        'success': False
                    })
            
            # Update session progress
            new_progress = min(100, int((end_idx / len(prompts)) * 100))
            session['progress'] = new_progress
            session['results'].extend(batch_results)
            
            if new_progress >= 100:
                session['status'] = 'completed'
                session['end_time'] = time.time()
            
            return {
                'success': True,
                'progress': new_progress,
                'batch_results': batch_results,
                'status': session['status']
            }
            
        except Exception as e:
            logger.error(f"Error processing training batch: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_training_status(self, session_id):
        """Get current training status"""
        session = self.training_sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        return {
            'success': True,
            'session_id': session_id,
            'status': session['status'],
            'progress': session['progress'],
            'model': session['model'],
            'languages': session['languages'],
            'start_time': session['start_time'],
            'results_count': len(session['results'])
        }
    
    def test_model_response(self, model_name, prompt, language='en'):
        """Test model response for given prompt"""
        try:
            if not self.is_configured():
                return {'success': False, 'error': 'Google AI not configured'}
            
            model = genai.GenerativeModel(self.models.get(model_name, 'gemini-1.5-pro-latest'))
            
            # Enhanced prompt with language and eco-context
            enhanced_prompt = f"""
            You are SynoMind, an eco-friendly AI assistant for the EcoSyno platform.
            Language: {language}
            User query: {prompt}
            
            Provide a helpful, environmentally conscious response that promotes sustainable living.
            """
            
            response = model.generate_content(enhanced_prompt)
            
            return {
                'success': True,
                'model': model_name,
                'language': language,
                'prompt': prompt,
                'response': response.text,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error testing model: {e}")
            return {'success': False, 'error': str(e)}

# Global service instance
google_ai_service = GoogleAITrainingService()

@google_ai_bp.route('/test-connection')
def test_google_ai_connection():
    """Test Google AI connection"""
    try:
        if not google_ai_service.is_configured():
            return jsonify({
                'success': False,
                'error': 'Google AI API key not configured'
            }), 400
        
        # Test with a simple prompt
        result = google_ai_service.test_model_response(
            'gemini-1.5-pro',
            'Hello, please introduce yourself as SynoMind.',
            'en'
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@google_ai_bp.route('/start-training', methods=['POST'])
def start_google_ai_training():
    """Start Google AI training session"""
    try:
        config = request.get_json()
        result = google_ai_service.start_voice_training(config)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@google_ai_bp.route('/training-status/<session_id>')
def get_google_training_status(session_id):
    """Get training status"""
    try:
        result = google_ai_service.get_training_status(session_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@google_ai_bp.route('/process-batch/<session_id>', methods=['POST'])
def process_google_training_batch(session_id):
    """Process training batch"""
    try:
        batch_size = request.get_json().get('batch_size', 3)
        result = google_ai_service.process_training_batch(session_id, batch_size)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500