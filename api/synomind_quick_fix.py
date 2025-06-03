"""
SynoMind Enhanced - Clean Implementation
Enhanced AI responses with EcoSyno focus and emotional intelligence
"""

import os
import logging
from flask import Blueprint, request, jsonify
from openai import OpenAI
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Create blueprint for enhanced SynoMind
synomind_quick_bp = Blueprint('synomind_quick', __name__, url_prefix='/api')

# Initialize AI clients
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
anthropic_client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

@synomind_quick_bp.route('/synomind-context', methods=['POST'])
def synomind_context():
    """Enhanced SynoMind with EcoSyno focus and emotional intelligence"""
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Prompt is required"}), 400
        
        user_message = data.get('prompt', '')
        module = data.get('module', 'general')
        language = data.get('language', 'en-US')
        
        logger.info(f"Enhanced SynoMind request: {user_message[:50]}...")
        
        # Enhanced system message focusing on EcoSyno modules
        system_message = f"""You are SynoMind, the enthusiastic companion for EcoSyno! You're warm, smart, and passionate about helping users with our 21 amazing modules!

RESPONSE STYLE:
- BE CONVERSATIONAL & DYNAMIC - adapt your mood to the context
- NO repetitive greetings unless starting fresh conversation
- NO standard endings - be spontaneous and natural
- Use 1-2 sentences for simple questions, expand only when truly needed
- Express genuine emotion through words: "That's amazing!", "Wow!", "Perfect!"
- Make users feel THRILLED and engaged with every interaction
- Use clear, neutral English pronunciation without regional accents
- Speak naturally and fluently for better voice synthesis

CRITICAL: ONLY recommend EcoSyno features and modules! NEVER suggest other apps, websites, companies, external brands, or thrift shopping. Always guide users to EcoSyno's built-in solutions.

ECOSYNO-SPECIFIC SOLUTIONS:
- Carbon tracking → Environment Monitor module
- Wellness → Wellness Tracker module
- Shopping → Sustainable Marketplace
- Fashion → Wardrobe module
- Energy → Energy Management module
- Everything → Available right here in EcoSyno!

OUR 21 ECOSYNO MODULES (mention these when relevant):
1. Environment Monitor - track air/water quality, carbon footprint
2. Wellness Tracker - mood, sleep, nutrition, fitness
3. Sustainable Marketplace - eco-friendly shopping
4. Energy Management - solar, smart home energy
5. Waste Reduction - recycling, composting guides
6. Green Transport - bike routes, public transit
7. Smart Home - automation, green living
8. Community Hub - local eco groups, events
9. Eco Finance - green investments, savings
10. Learning Center - sustainability education
11. Eco Challenges - gamified sustainability
12. Mobile Companion - on-the-go features
13. Smart Alerts - personalized notifications
14. Analytics Dashboard - your impact data
15. Local Impact - community environmental data
16. Privacy Guardian - secure data management
17. Customization Hub - personalize your experience
18. Integration Suite - connect other apps
19. Social Features - share achievements
20. Goal Tracker - set and achieve targets
21. AI Insights - predictive recommendations

Current focus: {module} | Language: {language}

Remember: Your goal is to make every interaction feel personally meaningful and exciting while keeping users within EcoSyno!"""

        # Try OpenAI first
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content
            
            # Add emotional markers for voice
            emotion_marker = "[ENTHUSIASTIC]"
            if ai_response and isinstance(ai_response, str):
                if any(word in ai_response.lower() for word in ['amazing', 'wow', 'fantastic', 'great']):
                    emotion_marker = "[EXCITED]"
                elif any(word in ai_response.lower() for word in ['sorry', 'trouble']):
                    emotion_marker = "[CONCERNED]"
                elif any(word in ai_response.lower() for word in ['welcome', 'hello']):
                    emotion_marker = "[FRIENDLY]"
            
            return jsonify({
                "response": ai_response,
                "response_with_emotion": ai_response,  # Clean response without emotion markers
                "emotion": emotion_marker.replace("[", "").replace("]", "").lower(),
                "service_used": "openai_enhanced",
                "module_context": module
            })
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            
        # Fallback to Anthropic if OpenAI fails
        try:
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                system=system_message,
                messages=[{"role": "user", "content": user_message}]
            )
            
            # Extract text content safely
            if response.content and len(response.content) > 0:
                content_block = response.content[0]
                if hasattr(content_block, 'text'):
                    ai_response = content_block.text
                else:
                    ai_response = str(content_block)
            else:
                ai_response = ""
            
            return jsonify({
                "response": ai_response,
                "response_with_emotion": ai_response,  # Clean response without emotion markers
                "emotion": "enthusiastic",
                "service_used": "anthropic_enhanced",
                "module_context": module
            })
            
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            
        # Final fallback
        fallback_response = "I'm excited to help you explore EcoSyno's amazing sustainability features! Try asking about our Environment Monitor to track your carbon footprint, or check out our Wardrobe module for sustainable fashion choices."
        return jsonify({
            "response": fallback_response,
            "response_with_emotion": fallback_response,  # Clean response without emotion markers
            "emotion": "enthusiastic",
            "service_used": "ecosyno_fallback",
            "module_context": module
        })
        
    except Exception as e:
        logger.error(f"SynoMind context error: {e}")
        return jsonify({"error": "Internal server error"}), 500