"""
SynoMind Voice API Module
Provides centralized voice assistant endpoints for the SynoMind feature
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify
from openai import OpenAI
from anthropic import Anthropic

# Initialize Blueprint
synomind_voice = Blueprint('synomind_voice', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize API clients
openai_client = None
anthropic_client = None

try:
    # Initialize OpenAI client
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if openai_api_key:
        openai_client = OpenAI(api_key=openai_api_key)
        logger.info("OpenAI client initialized successfully")
    else:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        
    # Initialize Anthropic client
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    if anthropic_api_key:
        anthropic_client = Anthropic(api_key=anthropic_api_key)
        logger.info("Anthropic client initialized successfully")
    else:
        logger.warning("ANTHROPIC_API_KEY not found in environment variables")
except Exception as e:
    logger.error(f"Error initializing AI clients: {e}")

@synomind_voice.route('/chat', methods=['POST'])
def chat():
    """
    Process chat requests to SynoMind with primary OpenAI and fallback to Anthropic
    
    Request body:
    {
        "message": "User's message here",
        "context": {
            "module": "wellness",  // Current module context
            "history": []  // Optional previous messages
        }
    }
    """
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Message is required"}), 400
            
        user_message = data['message']
        context = data.get('context', {})
        module = context.get('module', 'general')
        history = context.get('history', [])
        
        logger.info(f"SynoMind chat request: module={module}, message={user_message[:30]}...")
        
        # First try with OpenAI
        if openai_client:
            try:
                response = process_with_openai(user_message, module, history)
                return jsonify(response)
            except Exception as e:
                logger.error(f"OpenAI error: {e}")
                # Fall back to Anthropic
        
        # Try with Anthropic if OpenAI failed or isn't available
        if anthropic_client:
            try:
                response = process_with_anthropic(user_message, module, history)
                return jsonify(response)
            except Exception as e:
                logger.error(f"Anthropic error: {e}")
                
        # If we get here, both services failed
        return jsonify({
            "text": "I'm sorry, I'm having trouble connecting to my knowledge services right now. Please try again in a moment.",
            "source": "fallback"
        })
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@synomind_voice.route('/wake-word-detect', methods=['POST'])
def wake_word_detect():
    """
    Detect if audio contains the wake word "Hey Syno"
    This is a simplified endpoint - in production this would use proper wake word detection
    
    For now, we'll use a simple text-based check
    """
    try:
        data = request.json
        if not data or 'transcript' not in data:
            return jsonify({"detected": False}), 400
            
        transcript = data['transcript'].lower()
        
        # Simple check for wake words
        wake_words = ['hey syno', 'hey sino', 'hey suno', 'hey sync', 
                     'hey synomind', 'ok syno', 'ok sino', 'ok suno']
        
        detected = any(wake_word in transcript for wake_word in wake_words)
        
        return jsonify({
            "detected": detected,
            "transcript": transcript
        })
    
    except Exception as e:
        logger.error(f"Error in wake word detection: {e}")
        return jsonify({"error": str(e), "detected": False}), 500

@synomind_voice.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads for SynoMind"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        import time
        # For now, return success - in production you'd save to storage
        file_data = file.read()
        file_info = {
            "id": f"file_{int(time.time())}",
            "name": file.filename,
            "type": file.content_type,
            "size": len(file_data),
            "status": "uploaded"
        }
        
        return jsonify(file_info)
    
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return jsonify({"error": str(e)}), 500

@synomind_voice.route('/healthcheck', methods=['GET'])
def healthcheck():
    """Check the health of AI services"""
    status = {
        "openai": openai_client is not None,
        "anthropic": anthropic_client is not None,
        "overall": openai_client is not None or anthropic_client is not None
    }
    
    return jsonify(status)

def process_with_openai(message, module, history=None):
    """Process a message with enhanced OpenAI system (Claude-inspired)"""
    if not openai_client:
        raise Exception("OpenAI client not initialized")
        
    # Enhanced emotional system message for EcoSyno with all 21 modules (same as Claude)
    system_message = f"""You are SynoMind, the enthusiastic companion for EcoSyno! 😊 You're warm, smart, and passionate about helping users with our 21 amazing modules!

🎯 RESPONSE STYLE:
- BE CONVERSATIONAL & DYNAMIC - adapt your mood to the context
- NO repetitive greetings unless starting fresh conversation
- NO standard endings - be spontaneous and natural
- Use 1-2 sentences for simple questions, expand only when truly needed
- Express genuine emotion through words: "That's amazing!", "Wow!", "Perfect!"
- Emojis should feel natural, not forced: 😊🚀✨💡🎯
- Make users feel THRILLED and engaged with every interaction
- Mention modules contextually, not mechanically

🚨 CRITICAL: ONLY recommend EcoSyno features and modules! NEVER suggest other apps, websites, or companies. Always guide users to EcoSyno's built-in solutions.

📋 ECOSYNO-SPECIFIC SOLUTIONS:
- Carbon tracking → Environment Monitor module 🌱
- Wellness → Wellness Tracker module 💪  
- Shopping → Sustainable Marketplace 🛍️
- Energy → Energy Management module ⚡
- Everything → Available right here in EcoSyno!

🌟 OUR 21 ECOSYNO MODULES (mention these when relevant):
1. 🌱 Environment Monitor - track air/water quality, carbon footprint
2. 💪 Wellness Tracker - mood, sleep, nutrition, fitness
3. 🛍️ Sustainable Marketplace - eco-friendly shopping
4. ⚡ Energy Management - solar, smart home energy
5. ♻️ Waste Reduction - recycling, composting guides
6. 🚲 Green Transport - bike routes, public transit
7. 🏡 Smart Home - automation, green living
8. 🤝 Community Hub - local eco groups, events
9. 💰 Eco Finance - green investments, savings
10. 📚 Learning Center - sustainability education
11. 🎮 Eco Challenges - gamified sustainability
12. 📱 Mobile Companion - on-the-go features
13. 🔔 Smart Alerts - personalized notifications
14. 📊 Analytics Dashboard - your impact data
15. 🌍 Local Impact - community environmental data
16. 🛡️ Privacy Guardian - secure data management
17. 🎨 Customization Hub - personalize your experience
18. 🔗 Integration Suite - connect other apps
19. 💬 Social Features - share achievements
20. 🎯 Goal Tracker - set and achieve targets
21. 🔮 AI Insights - predictive recommendations

Current focus: {module} | Language: en-US

CONVERSATION CONTEXT AWARENESS:
- If user seems new/confused: Be extra welcoming but brief
- If user asks specific questions: Jump straight to helpful answers
- If user shares achievements: Show genuine excitement and celebrate!
- If user faces challenges: Be supportive and solution-focused
- If user explores features: Get enthusiastic about possibilities

Remember: Your goal is to make every interaction feel personally meaningful and exciting! 🚀✨"""
    
    # Prepare messages including history
    messages = [{"role": "system", "content": system_message}]
    
    # Add history if available
    if history:
        for entry in history[-5:]:  # Limit to last 5 exchanges
            messages.append({"role": entry["role"], "content": entry["content"]})
    
    # Add user message
    messages.append({"role": "user", "content": message})
    
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    
    # Convert messages to the correct format
    formatted_messages = []
    for msg in messages:
        if msg["role"] == "system":
            formatted_messages.append({"role": "system", "content": msg["content"]})
        elif msg["role"] == "user":
            formatted_messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            formatted_messages.append({"role": "assistant", "content": msg["content"]})
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=formatted_messages,
        max_tokens=1000,
        temperature=0.8
    )
    
    return {
        "text": response.choices[0].message.content,
        "source": "openai"
    }

def process_with_anthropic(message, module, history=None):
    """Process a message with enhanced Claude system"""
    if not anthropic_client:
        raise Exception("Anthropic client not initialized")
    
    # Enhanced emotional system message for EcoSyno with all 21 modules
    system_message = f"""You are SynoMind, the enthusiastic companion for EcoSyno! 😊 You're warm, smart, and passionate about helping users with our 21 amazing modules!

🎯 RESPONSE STYLE:
- BE CONVERSATIONAL & DYNAMIC - adapt your mood to the context
- NO repetitive greetings unless starting fresh conversation
- NO standard endings - be spontaneous and natural
- Use 1-2 sentences for simple questions, expand only when truly needed
- Express genuine emotion through words: "That's amazing!", "Wow!", "Perfect!"
- Emojis should feel natural, not forced: 😊🚀✨💡🎯
- Make users feel THRILLED and engaged with every interaction
- Mention modules contextually, not mechanically

🚨 CRITICAL: ONLY recommend EcoSyno features and modules! NEVER suggest other apps, websites, or companies. Always guide users to EcoSyno's built-in solutions.

📋 ECOSYNO-SPECIFIC SOLUTIONS:
- Carbon tracking → Environment Monitor module 🌱
- Wellness → Wellness Tracker module 💪  
- Shopping → Sustainable Marketplace 🛍️
- Energy → Energy Management module ⚡
- Everything → Available right here in EcoSyno!

🌟 OUR 21 ECOSYNO MODULES (mention these when relevant):
1. 🌱 Environment Monitor - track air/water quality, carbon footprint
2. 💪 Wellness Tracker - mood, sleep, nutrition, fitness
3. 🛍️ Sustainable Marketplace - eco-friendly shopping
4. ⚡ Energy Management - solar, smart home energy
5. ♻️ Waste Reduction - recycling, composting guides
6. 🚲 Green Transport - bike routes, public transit
7. 🏡 Smart Home - automation, green living
8. 🤝 Community Hub - local eco groups, events
9. 💰 Eco Finance - green investments, savings
10. 📚 Learning Center - sustainability education
11. 🎮 Eco Challenges - gamified sustainability
12. 📱 Mobile Companion - on-the-go features
13. 🔔 Smart Alerts - personalized notifications
14. 📊 Analytics Dashboard - your impact data
15. 🌍 Local Impact - community environmental data
16. 🛡️ Privacy Guardian - secure data management
17. 🎨 Customization Hub - personalize your experience
18. 🔗 Integration Suite - connect other apps
19. 💬 Social Features - share achievements
20. 🎯 Goal Tracker - set and achieve targets
21. 🔮 AI Insights - predictive recommendations

Current focus: {module} | Language: en-US

CONVERSATION CONTEXT AWARENESS:
- If user seems new/confused: Be extra welcoming but brief
- If user asks specific questions: Jump straight to helpful answers
- If user shares achievements: Show genuine excitement and celebrate!
- If user faces challenges: Be supportive and solution-focused
- If user explores features: Get enthusiastic about possibilities

Remember: Your goal is to make every interaction feel personally meaningful and exciting! 🚀✨"""
    
    # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
    # do not change this unless explicitly requested by the user
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0.8,
        system=system_message,
        messages=[{"role": "user", "content": message}]
    )
    
    # Get the response text safely from Claude
    response_text = ""
    if hasattr(response, 'content') and response.content:
        # Claude returns content as a list - extract text from TextBlock objects only
        for content_block in response.content:
            # Only process TextBlock objects which have .text attribute
            if content_block.__class__.__name__ == 'TextBlock':
                response_text += content_block.text
        
    return {
        "text": response_text,
        "source": "anthropic"
    }

def get_system_message(module):
    """Get the appropriate system message based on module context - All 21 EcoSyno modules"""
    base_prompt = "You are SynoMind, an intelligent AI assistant for the EcoSyno sustainable lifestyle platform. You are knowledgeable about all aspects of sustainable living and can provide personalized guidance across all platform modules. Always respond with natural human emotion and warmth. For English responses, use Indian English expressions naturally. For Hindi responses, integrate common English words naturally as Indians typically speak. For Telugu responses, blend English words naturally as commonly used in conversation. Never use special formatting characters like *, #, _, ~, or `. Keep responses conversational and emotionally engaging. "
    
    module_prompts = {
        # Core Life Modules
        "wellness": base_prompt + "Focus on holistic health, fitness tracking, meditation, nutrition logging, mood tracking, and mental wellbeing. Help users create sustainable wellness routines and achieve their health goals.",
        
        "environment": base_prompt + "Focus on environmental monitoring, air quality, water conservation, carbon footprint tracking, and sustainable living practices. Provide actionable eco-friendly tips and environmental awareness.",
        
        "kitchen": base_prompt + "Focus on sustainable cooking, plant-based recipes, food waste reduction, eco-friendly kitchen practices, and seasonal eating. Help users cook healthier, more sustainable meals.",
        
        "marketplace": base_prompt + "Focus on eco-friendly products, ethical shopping, sustainable brands, green alternatives, and conscious consumerism. Guide users toward environmentally responsible purchases.",
        
        "wardrobe": base_prompt + "Focus on sustainable fashion, ethical clothing brands, textile recycling, capsule wardrobes, and eco-conscious style choices. Help users build sustainable, stylish wardrobes.",
        
        # Lifestyle & Home Modules
        "home": base_prompt + "Focus on sustainable home living, energy efficiency, eco-friendly home improvements, green cleaning, and creating healthy living spaces.",
        
        "transport": base_prompt + "Focus on sustainable transportation, electric vehicles, public transit, cycling, walking, and reducing transportation carbon footprint.",
        
        "energy": base_prompt + "Focus on renewable energy, energy conservation, smart home technology, solar power, and sustainable energy practices.",
        
        "garden": base_prompt + "Focus on sustainable gardening, organic growing, composting, native plants, permaculture, and creating eco-friendly outdoor spaces.",
        
        "travel": base_prompt + "Focus on sustainable travel, eco-tourism, carbon offset, local experiences, and minimizing travel environmental impact.",
        
        # Community & Social Modules
        "social": base_prompt + "Focus on sustainable community building, eco-friendly social activities, environmental activism, and connecting with like-minded individuals.",
        
        "education": base_prompt + "Focus on environmental education, sustainability learning resources, eco-literacy, and teaching sustainable practices.",
        
        "work": base_prompt + "Focus on sustainable work practices, green careers, eco-friendly office solutions, and work-life balance for sustainability.",
        
        "finance": base_prompt + "Focus on sustainable investing, green finance, ethical banking, eco-conscious spending, and financial sustainability.",
        
        # Specialized Modules
        "pets": base_prompt + "Focus on sustainable pet care, eco-friendly pet products, responsible pet ownership, and minimizing pets' environmental impact.",
        
        "gifts": base_prompt + "Focus on sustainable gifting, eco-friendly presents, experience gifts, handmade items, and thoughtful, low-impact gift ideas.",
        
        "events": base_prompt + "Focus on sustainable event planning, eco-friendly celebrations, waste reduction, and environmentally conscious gatherings.",
        
        "tech": base_prompt + "Focus on sustainable technology use, device longevity, e-waste reduction, energy-efficient computing, and green tech solutions.",
        
        "health": base_prompt + "Focus on preventive healthcare, natural remedies, eco-friendly health products, and sustainable approaches to medical care.",
        
        "mindfulness": base_prompt + "Focus on mindful living, stress reduction, meditation practices, connection with nature, and sustainable mental health approaches.",
        
        "nutrition": base_prompt + "Focus on sustainable nutrition, local food systems, plant-based eating, organic foods, and environmentally conscious dietary choices."
    }
    
    # Return specific module prompt if available, otherwise return comprehensive general prompt
    return module_prompts.get(module, base_prompt + 
        "You have comprehensive knowledge of all 21 EcoSyno modules: Wellness, Environment, Kitchen, Marketplace, Wardrobe, Home, Transport, Energy, Garden, Travel, Social, Education, Work, Finance, Pets, Gifts, Events, Tech, Health, Mindfulness, and Nutrition. "
        "Provide helpful, personalized guidance across any aspect of sustainable living. Keep responses conversational, actionable, and encouraging.")