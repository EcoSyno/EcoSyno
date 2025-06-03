import os
import logging
import json
import jwt
import uuid
from flask import jsonify, send_from_directory, render_template, request, redirect, make_response
from flask_jwt_extended import JWTManager, decode_token
# Fallback mode removed - using clean admin system

# Import the Flask app and database from app.py
from app import app, db

# Domain manager disabled to fix ERR_TOO_MANY_REDIRECTS
# Completely disabled to prevent any redirect loops
print("✅ Domain redirect system disabled - ecosyno.com should work now")
print("📧 Contact available at /contact")

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure N8N webhook URL for Telugu voice processing
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', 'http://localhost:5678/webhook/process-telugu')

# Initialize JWT
jwt = JWTManager(app)

# Import clean architecture components
from core.service_registry import service_registry

# Remove conflicting admin system temporarily
# from single_admin import register_single_admin
from auth_middleware import token_required, admin_required, super_admin_required, ROLE_SUPER_ADMIN

# Admin system will be handled separately to avoid conflicts

# Add simple environment detection based on subdomain
# Subdomain detection disabled to fix redirect loops
# @app.before_request
def detect_environment_disabled():
    """Environment detection disabled to prevent redirect issues"""
    # Set default production environment
    app.config['CURRENT_ENVIRONMENT'] = 'PRODUCTION'
    app.config['ENV_COLOR'] = '#dc3545'
    app.config['ENV_NAME'] = 'Production'

# Register organized route blueprints
try:
    from routes.module_routes import module_routes
    from routes.api_routes import api_routes
    from routes.dashboard_routes import dashboard_routes
    from routes.workflow_routes import workflow_routes
    from routes.core_routes import core_routes
    
    service_registry.register_blueprint(app, module_routes)
    service_registry.register_blueprint(app, api_routes)
    service_registry.register_blueprint(app, dashboard_routes)
    service_registry.register_blueprint(app, workflow_routes)
    service_registry.register_blueprint(app, core_routes)
    
    # Register smart local processing API
    from api.smart_local_processing import smart_local_bp
    service_registry.register_blueprint(app, smart_local_bp)
    
    # Register unified login system
    from routes.unified_login import unified_login
    service_registry.register_blueprint(app, unified_login)
    
    # Register existing admin system
    from api.admin import register_admin_routes
    register_admin_routes(app)
    
    # Removed separate admin login - using unified login system
    
    # Register super admin routes for training
    from routes.super_admin_routes import super_admin_routes
    service_registry.register_blueprint(app, super_admin_routes)
    
    # Register testing environment for users
    from routes.testing_environment_routes import testing_env_routes
    service_registry.register_blueprint(app, testing_env_routes)
    
    # Register QA environment for comprehensive testing
    from routes.qa_environment_routes import qa_env_routes
    service_registry.register_blueprint(app, qa_env_routes)
    
    # Register UAT environment routes
    from routes.uat_environment_routes import uat_env_routes
    service_registry.register_blueprint(app, uat_env_routes)
    
    # Register Demo environment routes
    from routes.demo_environment_routes import demo_env_routes
    service_registry.register_blueprint(app, demo_env_routes)
    
    # Register development environment for uninterrupted coding
    from routes.dev_environment_routes import dev_env_routes
    service_registry.register_blueprint(app, dev_env_routes)
    
    # Register working SynoMind quick fix
    from api.synomind_quick_fix import synomind_quick_bp
    service_registry.register_blueprint(app, synomind_quick_bp)
    
    # Register SynoMind Training API
    from api.synomind_training_api import synomind_training_api
    from api.training_logs import register_training_logs
    service_registry.register_blueprint(app, synomind_training_api)
    register_training_logs(app)
    
    logger.info("Organized route blueprints registered successfully")
except ImportError as e:
    logger.warning(f"Could not import organized routes: {e}")
    # Continue without organized routes for now

# Temporarily disabled to prevent conflicts
# from api.admin import register_admin_routes
# register_admin_routes(app)

# Import charts module through service registry
from charts_integration import register_charts_module
register_charts_module(app)

# Import and register AI integrations for SynoMind
try:
    # Register OpenAI voice integration
    from api.openai_voice import register_openai_voice
    register_openai_voice(app)
    logger.info("OpenAI voice integration registered successfully")
    
    # Register Claude voice integration
    from api.claude_voice import register_claude_voice
    register_claude_voice(app)
    logger.info("Claude voice integration registered successfully")
    
    # Register Premium AI Service through service registry
    from api.premium_ai_service import premium_ai_bp
    service_registry.register_blueprint(app, premium_ai_bp, url_prefix='/api/premium_ai')
    logger.info("Premium AI service registered successfully")
    
    # Register Llama model integration through service registry
    from api.llama_model import llama_bp
    service_registry.register_blueprint(app, llama_bp, url_prefix='/api/llama')
    logger.info("Llama model integration registered successfully")
    
    # Register SynoMind unified voice assistant
    from api.synomind_voice import synomind_voice
    service_registry.register_blueprint(app, synomind_voice, url_prefix='/api/synomind_voice')
    logger.info("SynoMind unified voice assistant registered successfully")
    
    # Register Local Models Training API
    from api.local_models_training import local_models_bp
    service_registry.register_blueprint(app, local_models_bp, url_prefix='/api/local-models')
    logger.info("Local models training API registered successfully")
    
    # Register Roo Code Agents
    from api.roo_code_agents import register_roo_agents
    register_roo_agents(app)
    logger.info("Roo code agents registered successfully")
    
    # Register Real AI Agents
    from api.real_agents_api import register_real_agents
    register_real_agents(app)
    logger.info("Real AI agents registered successfully")
    
    # Register Agent Recommendations API
    from api.agent_recommendations_api import register_agent_recommendations_api
    register_agent_recommendations_api(app)
    logger.info("Agent Recommendations API registered successfully")
except Exception as e:
    logger.error(f"Failed to register AI integrations: {str(e)}")

# Import and register API modules with unique names to avoid conflicts
try:
    from api.wellness import wellness_bp
    app.register_blueprint(wellness_bp, url_prefix='/api/wellness', name='api_wellness')
    
    # Register Wellness Dashboard API for dynamic functionality
    from api.wellness_dashboard import wellness_dashboard_bp
    app.register_blueprint(wellness_dashboard_bp, url_prefix='/api/wellness-dashboard', name='api_wellness_dashboard')
    
    from api.environment import environment_bp
    app.register_blueprint(environment_bp, url_prefix='/api/environment', name='api_environment')
    
    from api.marketplace import marketplace_bp
    app.register_blueprint(marketplace_bp, url_prefix='/api/marketplace', name='api_marketplace')
    
    from api.kitchen import kitchen_bp
    app.register_blueprint(kitchen_bp, url_prefix='/api/kitchen', name='api_kitchen')
    
    from api.wardrobe import wardrobe_bp
    app.register_blueprint(wardrobe_bp, url_prefix='/api/wardrobe', name='api_wardrobe')
    
    # Register AI Gateway
    from ai_gateway import ai_gateway_bp
    app.register_blueprint(ai_gateway_bp, url_prefix='/api/ai', name='ai_gateway')
    
    # Register SynoMind Camera API
    from api.synomind_camera import synomind_camera_bp
    app.register_blueprint(synomind_camera_bp)
    
    # Register N8N Workflow Manager API
    try:
        from api.workflow_manager import register_n8n_workflow_module
        register_n8n_workflow_module(app)
        
        # Register Document Analysis API with Premium AI Integration
        from api.document_analysis import document_analysis
        app.register_blueprint(document_analysis, url_prefix='/api/premium-ai')
        logger.info("Document Analysis API with Premium AI registered successfully")
        logger.info("N8N Workflow Manager registered successfully")
    except Exception as e:
        logger.error(f"Failed to register N8N Workflow Manager: {str(e)}")
    
    logger.info("API modules registered successfully")
    
    # Register Google AI integration
    from google_ai_service import register_google_ai
    register_google_ai(app)
    logger.info("Google AI integration registered successfully")
    
    # Register Google AI Training service
    from api.google_ai_training import google_ai_bp
    service_registry.register_blueprint(app, google_ai_bp, url_prefix='/api/google-ai-training')
    logger.info("Google AI Training service with real Gemini API registered successfully")
    
    # Register SDLC & ALM Agent Ecosystem
    from api.sdlc_agents import register_sdlc_agents
    register_sdlc_agents(app)
    logger.info("SDLC & ALM Agent Ecosystem registered successfully")
    
    # Register Comprehensive AI Models Integration
    from api.comprehensive_ai_models import register_comprehensive_ai_models
    register_comprehensive_ai_models(app)
    logger.info("Comprehensive AI Models integration registered successfully")
    
    # Register Comprehensive Testing Agents Ecosystem
    from api.comprehensive_testing_agents import register_comprehensive_testing_agents
    register_comprehensive_testing_agents(app)
    logger.info("Comprehensive Testing Agents ecosystem registered successfully")
    
    # Fresh admin system is already registered above
    logger.info("Fresh admin authentication system registered successfully")
except Exception as e:
    logger.error(f"Error registering API modules: {str(e)}")

# Create all database tables
with app.app_context():
    try:
        # Import models to ensure they're registered with SQLAlchemy
        from models import (
            User, WaterQualityEntry, Plant, PlantHealthLog,
            FridgeItem, GroceryList, GroceryItem,
            ClothingItem, LaundryLog, Outfit,
            MarketplaceItem, MarketplaceOrder, MarketplaceReview,
            MoodLog, SleepRecord, MeditationSession
        )
        
        # Create tables
        db.create_all()
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database tables: {str(e)}")

@app.route('/admin-direct')
def admin_direct_login():
    """Direct admin login page that bypasses all conflicts"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>EcoSyno Admin Login - Working</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            margin: 0; 
            padding: 20px; 
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .container { 
            background: white; 
            padding: 40px; 
            border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            max-width: 500px; 
            width: 100%; 
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 30px; 
            font-size: 28px;
        }
        .status { 
            background: #e8f5e8; 
            color: #2e7d32; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0; 
            text-align: center;
            border: 2px solid #4caf50;
        }
        input { 
            width: 100%; 
            padding: 15px; 
            margin: 10px 0; 
            border: 2px solid #ddd; 
            border-radius: 8px; 
            box-sizing: border-box; 
            font-size: 16px; 
        }
        button { 
            width: 100%; 
            padding: 15px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 18px; 
            font-weight: bold; 
            margin-top: 20px;
        }
        button:hover { 
            transform: translateY(-2px); 
        }
        .message { 
            text-align: center; 
            margin: 20px 0; 
            padding: 10px;
            border-radius: 5px;
        }
        .success { 
            background: #e8f5e8; 
            color: #2e7d32; 
            border: 1px solid #4caf50;
        }
        .error { 
            background: #ffebee; 
            color: #c62828; 
            border: 1px solid #ef5350;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌱 EcoSyno Admin Access</h1>
        
        <div class="status">
            ✅ Direct Login Ready - No External Dependencies
        </div>
        
        <form id="loginForm">
            <input type="email" id="email" placeholder="Admin Email" value="superadmin@ecosyno.com" required>
            <input type="password" id="password" placeholder="Admin Password" value="qxO%&6soq0Wg^74%M4UO" required>
            <button type="submit" id="loginBtn">Login to Admin Dashboard</button>
        </form>
        
        <div id="message"></div>
    </div>
    
    <script>
        document.getElementById('loginForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const message = document.getElementById('message');
            const btn = document.getElementById('loginBtn');
            
            btn.disabled = true;
            btn.textContent = 'Logging in...';
            message.innerHTML = '<div class="message">Authenticating...</div>';
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({email: email, password: password})
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    message.innerHTML = '<div class="message success">✅ Login successful! Redirecting...</div>';
                    
                    if (data.access_token) {
                        localStorage.setItem('ecosyno_token', data.access_token);
                        localStorage.setItem('ecosyno_user', JSON.stringify(data.user));
                    }
                    
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1500);
                    
                } else {
                    message.innerHTML = '<div class="message error">❌ ' + (data.message || 'Login failed') + '</div>';
                    btn.disabled = false;
                    btn.textContent = 'Login to Admin Dashboard';
                }
                
            } catch (error) {
                console.error('Login error:', error);
                message.innerHTML = '<div class="message error">❌ Connection error. Please try again.</div>';
                btn.disabled = false;
                btn.textContent = 'Login to Admin Dashboard';
            }
        };
    </script>
</body>
</html>
    """

@app.route('/debug/routes')
def debug_routes():
    """Show all routes for debugging"""
    routes = []
    for rule in app.url_map.iter_rules():
        methods = []
        if rule.methods is not None:
            methods = sorted([method for method in rule.methods if method not in ["OPTIONS", "HEAD"]])
        routes.append({
            "endpoint": rule.endpoint,
            "methods": methods,
            "path": rule.rule
        })
    return jsonify(sorted(routes, key=lambda x: x["path"]))

# Redirect old admin routes to unified system
@app.route('/main-login', methods=['GET', 'POST'])
def simple_admin_login():
    """Simple working admin login"""
    if request.method == 'GET':
        return """
<!DOCTYPE html>
<html>
<head>
    <title>EcoSyno Admin Login</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 50px; min-height: 100vh; }
        .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        h2 { color: #333; text-align: center; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
        input:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; }
        button:hover { transform: translateY(-2px); }
        .credentials { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; font-size: 14px; border-left: 4px solid #667eea; }
        .error { color: #e74c3c; text-align: center; margin: 10px 0; }
        .success { color: #27ae60; text-align: center; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🌱 EcoSyno Admin</h2>
        <div class="credentials">
            <strong>Test Credentials:</strong><br>
            Email: superadmin@ecosyno.com<br>
            Password: qxO%&6soq0Wg^74%M4UO
        </div>
        <form id="loginForm">
            <input type="email" id="email" placeholder="Email" value="superadmin@ecosyno.com" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div id="message"></div>
    </div>
    
    <script>
        document.getElementById('loginForm').onsubmit = async function(e) {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const msg = document.getElementById('message');
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    msg.innerHTML = '<div class="success">✓ Login successful! Redirecting...</div>';
                    localStorage.setItem('access_token', data.access_token);
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1000);
                } else {
                    msg.innerHTML = '<div class="error">✗ ' + data.message + '</div>';
                }
            } catch (error) {
                msg.innerHTML = '<div class="error">✗ Connection error</div>';
            }
        };
    </script>
</body>
</html>
        """
    
    # Handle POST request
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Simple credential check
        if email == 'superadmin@ecosyno.com' and password == 'qxO%&6soq0Wg^74%M4UO':
            from flask_jwt_extended import create_access_token
            access_token = create_access_token(
                identity=email,
                additional_claims={'role': 'superadmin'}
            )
            return jsonify({
                'status': 'success',
                'access_token': access_token,
                'user': {
                    'email': email,
                    'role': 'superadmin'
                }
            })
        
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard')
def admin_dashboard():
    """Simple admin dashboard"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>EcoSyno Admin Dashboard</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card h3 { color: #333; margin-top: 0; }
        .btn { padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px; }
        .btn:hover { background: #5a6fd8; }
        .status { background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌱 EcoSyno Admin Dashboard</h1>
        <p>Welcome, Super Administrator</p>
    </div>
    
    <div class="status">
        ✅ Successfully logged in as Super Admin
    </div>
    
    <div class="dashboard-grid">
        <div class="card">
            <h3>System Status</h3>
            <p>All systems operational</p>
            <a href="/api/healthcheck" class="btn">Health Check</a>
        </div>
        
        <div class="card">
            <h3>User Management</h3>
            <p>Manage platform users and roles</p>
            <a href="/debug/routes" class="btn">View Routes</a>
        </div>
        
        <div class="card">
            <h3>SynoMind AI</h3>
            <p>AI assistant management</p>
            <a href="/api/synomind" class="btn">AI Console</a>
        </div>
        
        <div class="card">
            <h3>Platform Modules</h3>
            <p>21 sustainability modules</p>
            <a href="/app/ecosyno-hub" class="btn">Module Hub</a>
        </div>
    </div>
    
    <script>
        // Store admin status
        localStorage.setItem('admin_logged_in', 'true');
        localStorage.setItem('user_role', 'superadmin');
    </script>
</body>
</html>
    """

# Create API documentation for landing page
def get_api_docs():
    """Generate API documentation"""
    api_modules = [
        {
            'name': 'Authentication',
            'prefix': '/auth',
            'endpoints': [
                {'path': '/register', 'method': 'POST', 'description': 'Register a new EcoUser with PIN'},
                {'path': '/login', 'method': 'POST', 'description': 'Login with UID and PIN'},
                {'path': '/admin/login', 'method': 'POST', 'description': 'Admin login with email and password'}
            ]
        },
        {
            'name': 'Wellness',
            'prefix': '/api/wellness',
            'endpoints': [
                {'path': '/mood', 'method': 'POST', 'description': 'Log your current mood'},
                {'path': '/mood', 'method': 'GET', 'description': 'Get your mood history'},
                {'path': '/goals', 'method': 'POST', 'description': 'Create a wellness goal'}
            ]
        },
        {
            'name': 'Environment',
            'prefix': '/api/environment',
            'endpoints': [
                {'path': '/water', 'method': 'POST', 'description': 'Add water quality reading'},
                {'path': '/water', 'method': 'GET', 'description': 'Get water readings history'},
                {'path': '/plants', 'method': 'POST', 'description': 'Log plant status'},
                {'path': '/plants', 'method': 'GET', 'description': 'Get plant logs history'}
            ]
        },
        {
            'name': 'Kitchen',
            'prefix': '/api/kitchen',
            'endpoints': [
                {'path': '/grocery/receipts', 'method': 'POST', 'description': 'Upload a grocery receipt'},
                {'path': '/grocery/receipts', 'method': 'GET', 'description': 'Get your grocery receipts'},
                {'path': '/fridge', 'method': 'GET', 'description': 'Get your fridge items'},
                {'path': '/fridge/:item_id', 'method': 'PUT', 'description': 'Update a fridge item'},
                {'path': '/fridge/:item_id', 'method': 'DELETE', 'description': 'Delete a fridge item'}
            ]
        },
        {
            'name': 'Wardrobe',
            'prefix': '/api/wardrobe',
            'endpoints': [
                {'path': '/suggest-outfit', 'method': 'GET', 'description': 'Get outfit suggestions'},
                {'path': '/laundry', 'method': 'POST', 'description': 'Log laundry session'},
                {'path': '/laundry', 'method': 'GET', 'description': 'Get laundry history'},
                {'path': '/condition', 'method': 'GET', 'description': 'Get wardrobe condition'}
            ]
        },
        {
            'name': 'Marketplace',
            'prefix': '/api/marketplace',
            'endpoints': [
                {'path': '/items', 'method': 'GET', 'description': 'Browse available items'},
                {'path': '/orders', 'method': 'POST', 'description': 'Place a new order'},
                {'path': '/orders', 'method': 'GET', 'description': 'Get your order history'},
                {'path': '/orders/:order_number', 'method': 'GET', 'description': 'Get order details'},
                {'path': '/delivery-hubs', 'method': 'GET', 'description': 'Get available delivery hubs'}
            ]
        }
    ]
    
    # Generate documentation as HTML for simplicity
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EcoSyno API Documentation</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <style>
            body {
                padding: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }
            .module {
                margin-bottom: 30px;
            }
            .endpoint {
                margin-bottom: 10px;
            }
            .method {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 4px;
                font-weight: bold;
                width: 60px;
                text-align: center;
            }
            .method-get {
                background-color: var(--bs-info);
                color: var(--bs-dark);
            }
            .method-post {
                background-color: var(--bs-success);
                color: var(--bs-white);
            }
            .method-put {
                background-color: var(--bs-warning);
                color: var(--bs-dark);
            }
            .method-delete {
                background-color: var(--bs-danger);
                color: var(--bs-white);
            }
            .path {
                font-family: monospace;
                background-color: var(--bs-dark);
                padding: 3px 8px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body data-bs-theme="dark">
        <div class="container">
            <header class="py-4">
                <h1 class="mb-3">EcoSyno API Documentation</h1>
                <p class="lead">This page documents the available API endpoints for the EcoSyno sustainable lifestyle application.</p>
            </header>
            
            <main>
    """
    
    # Generate API modules HTML
    for module in api_modules:
        html += f"""
                <div class="module card mb-4">
                    <div class="card-header">
                        <h2 class="h4 mb-0">{module['name']}</h2>
                    </div>
                    <div class="card-body">
                        <p>Base URL: <code>{module['prefix']}</code></p>
                        <div class="endpoints">
        """
        
        for endpoint in module['endpoints']:
            method_class = f"method-{endpoint['method'].lower()}"
            html += f"""
                            <div class="endpoint d-flex align-items-center mb-2">
                                <span class="method {method_class} me-2">{endpoint['method']}</span>
                                <span class="path me-3">{module['prefix']}{endpoint['path']}</span>
                                <span class="description">{endpoint['description']}</span>
                            </div>
            """
            
        html += """
                        </div>
                    </div>
                </div>
        """
    
    # Close HTML
    html += """
            </main>
            
            <footer class="py-4 border-top">
                <p>© 2025 EcoSyno. All rights reserved.</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    return html

# Create routes for frontend
@app.route('/')
def index():
    """Serve React frontend or API documentation"""
    # Check if we're specifically requesting API docs
    if request.args.get('api_docs'):
        return get_api_docs()
    
    # Check if frontend is built
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    
    # If frontend is not built, serve our custom index page
    response = make_response(render_template('index.html', n8n_webhook_url=N8N_WEBHOOK_URL))
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/cache-bypass-test')
def cache_bypass_test():
    """Test endpoint with cache-busting headers"""
    response = make_response(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Cache Bypass Test</title></head>
    <body>
        <h1>✅ Server Working - {request.headers.get('Host')}</h1>
        <p>Time: {__import__('datetime').datetime.now()}</p>
        <p>If you see this correctly, the issue is Cloudflare cache corruption.</p>
    </body>
    </html>
    """)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/redirect-test')
def redirect_test():
    """Simple test page to diagnose redirect issues"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EcoSyno Redirect Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .status {{ background: #4CAF50; color: white; padding: 20px; border-radius: 8px; }}
            .info {{ background: #2196F3; color: white; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="status">
            <h1>✅ Server Working Correctly</h1>
            <p>If you can see this page, the EcoSyno server is working properly.</p>
        </div>
        
        <div class="info">
            <h3>Test Results:</h3>
            <p><strong>Host:</strong> {request.headers.get('Host', 'Unknown')}</p>
            <p><strong>User Agent:</strong> {request.headers.get('User-Agent', 'Unknown')[:100]}...</p>
            <p><strong>Protocol:</strong> {request.scheme}</p>
            <p><strong>URL:</strong> {request.url}</p>
        </div>
        
        <div class="info">
            <h3>Next Steps:</h3>
            <p>1. If this page loads on ecosyno.com/redirect-test, the issue is Cloudflare configuration</p>
            <p>2. Check Cloudflare Page Rules for redirect loops</p>
            <p>3. Disable "Always Use HTTPS" temporarily</p>
            <p>4. Set SSL mode to "Full" not "Flexible"</p>
        </div>
        
        <p><a href="/">← Back to Home</a></p>
    </body>
    </html>
    """

@app.route('/test-api')
def test_api():
    """Serve the test API page"""
    return render_template('test_api.html', n8n_webhook_url=N8N_WEBHOOK_URL)

@app.route('/synomind-demo')
def synomind_demo():
    """Direct route to SynoMind demo page with all enhanced features"""
    return render_template('direct_synomind_integrated.html', n8n_webhook_url=N8N_WEBHOOK_URL)

@app.route('/real-ai-agents')
def real_ai_agents_dashboard():
    """Real AI Agents Dashboard - Interactive Frontend"""
    return render_template('real_ai_agents_dashboard.html')

@app.route('/dashboard')
def user_dashboard():
    """Redirect to the EcoSyno Hub as the main dashboard"""
    return redirect('/app/ecosyno-hub')

# Serve frontend static files
@app.route('/assets/<path:path>')
def serve_assets(path):
    """Serve frontend static assets"""
    return send_from_directory('frontend/dist/assets', path)

# Handle React routes (catch-all for client-side routing)
@app.route('/app/dashboard')
def app_dashboard():
    """Redirect to the EcoSyno Hub as the main dashboard"""
    return redirect('/app/ecosyno-hub')

@app.route('/app/dashboard-legacy')
def app_dashboard_legacy():
    """Serve the legacy user dashboard page if needed"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('dashboard_unified.html')

@app.route('/app/ecosyno-hub')
def ecosyno_hub():
    """Serve the EcoSyno Hub - a comprehensive central command center"""
    return render_template('modules/ecosyno_hub.html')

@app.route('/app/module/ecosyno-modules', methods=['GET', 'POST'])
def ecosyno_modules():
    """
    Redirect to the EcoSyno Hub with All Modules tab active
    Note: This standalone page is deprecated and completely replaced by the All Modules tab in the hub
    """
    # Get token from either URL parameter, form data or cookies to ensure auth is preserved
    token = request.args.get('token') or request.form.get('token') or request.cookies.get('token', '')
    
    # Always redirect to the hub page with the modules tab active
    base_url = '/app/ecosyno-hub?active_tab=modules'
    
    # If token exists, add it to the redirect URL
    if token:
        redirect_url = f"{base_url}&token={token}"
        response = make_response(redirect(redirect_url))
        # Only set cookie if not already present
        if 'token' not in request.cookies:
            response.set_cookie('token', token, httponly=True, secure=True)
        return response
    
    return redirect(base_url)

@app.route('/direct-login')
def direct_login():
    """Emergency direct login access - bypasses authentication for testing"""
    app.logger.info("Direct login page accessed")
    return render_template('auth/direct_login.html')

@app.route('/app/admin/dashboard')
@admin_required
def admin_dashboard_app():
    """Serve the admin dashboard page"""
    return render_template('admin/new_dashboard.html')

@app.route('/app/admin/workflows')
@admin_required
def admin_workflows():
    """Serve the workflow manager page"""
    n8n_base_url = os.environ.get('N8N_BASE_URL', 'http://localhost:5678')
    return render_template('admin/workflow_manager.html', n8n_base_url=n8n_base_url)

@app.route('/app/<path:path>')
@token_required
def serve_react_routes(path):
    """Serve React app for any /app routes to handle client-side routing"""
    # Skip paths that are explicitly handled
    if path == 'dashboard':
        return app_dashboard()
    elif path == 'admin/dashboard':
        return admin_dashboard_app()
        
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        # For admin routes, use admin dashboard (with admin check)
        if path.startswith('admin/'):
            # Get current user from token
            current_user = getattr(request, 'user', None)
            # Check if user is admin
            if current_user and current_user.role in ['admin', 'super_admin']:
                return render_template('admin/new_dashboard.html')
            else:
                return redirect('/auth/login?error=unauthorized_access&redirect=/app/admin/' + path)
        # For user routes, use user dashboard
        else:
            return render_template('user_dashboard.html')

# Additional React routes specified in the application overview
@app.route('/login')
@app.route('/register')
@app.route('/unauthorized')
@app.route('/404')
@app.route('/error')
def serve_react_auth_routes():
    """Serve React app for auth and system routes"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        # For login, use the unified admin/super-admin login interface
        if request.path == '/login':
            return redirect('/login/')
        elif request.path == '/register':
            return redirect('/auth/register')
        else:
            return redirect('/')

# Handle all React role-specific routes
@app.route('/app/viewer/<path:path>')
@app.route('/app/user/<path:path>')
@app.route('/app/admin/<path:path>')
@app.route('/app/superadmin/<path:path>')
def serve_role_routes(path):
    """Serve React app for role-specific routes"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return redirect('/test-api')

# Handle SynoMind module routes
@app.route('/app/synomind')
@app.route('/app/module/synomind/assistant')
def synomind_module():
    """Serve SynoMind module with AI assistant"""
    # Log info for debugging
    app.logger.info("SynoMind module accessed without token validation")
    
    # Check for admin mode
    admin_mode = request.args.get('admin') == 'true'
    
    # For demonstration, SynoMind module is accessible without authentication
    # In a production environment, this would use proper authentication
    return render_template('modules/synomind.html', is_admin=admin_mode)

# Wellness Demo with SynoMind Integration
@app.route('/app/wellness-demo')
def wellness_demo():
    """Serve Wellness module demo with SynoMind integration"""
    app.logger.info("Wellness demo with SynoMind integration accessed")
    return render_template('modules/wellness_demo.html')

# Dynamic Wellness Dashboard
@app.route('/app/wellness-dashboard')
def wellness_dashboard_view():
    """Serve dynamic Wellness Dashboard with real data"""
    app.logger.info("Dynamic Wellness Dashboard accessed")
    return render_template('modules/wellness_dashboard.html')
        
# SynoMind Test Interface - accessible without authentication for testing
@app.route('/synomind-test')
def synomind_test():
    """Serve SynoMind test interface"""
    return render_template('synomind_test.html')

@app.route('/app/wellness')
def wellness_module_legacy():
    """Serve Wellness module (legacy route)"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/wellness_unified.html')

@app.route('/app/module/wellness')
def wellness_module():
    """Serve Wellness module with unified tabs interface"""
    # Log access attempt
    app.logger.info("Wellness module accessed")
    
    # First, check for admin status from URL param for testing
    if request.args.get('admin') == 'true':
        app.logger.info("Admin access granted via URL parameter (testing only)")
        return render_template('modules/wellness_unified.html', is_admin=True)
    
    # Get token from request
    token = request.args.get('token') or request.cookies.get('token')
    user_id = None
    
    if token:
        try:
            # Try to decode the token
            decoded = jwt.decode(token, app.config.get('JWT_SECRET_KEY'), algorithms=["HS256"])
            user_id = decoded.get('uid')
            app.logger.info(f"Wellness module accessed with token, user: {user_id}")
        except Exception as e:
            app.logger.warning(f"Invalid token for wellness module: {str(e)}")
    
    # Always allow access for demonstration purposes
    return render_template('modules/wellness_unified.html', is_admin=True)
    
    # Get JWT token and check for admin role (commented out for now)
    token = None
    
    # Try to get token from various sources
    if 'x-access-token' in request.headers:
        token = request.headers['x-access-token']
    elif 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    elif request.cookies.get('token'):
        token = request.cookies.get('token')
        
    app.logger.info(f"Wellness module accessed with token: {token[:10] if token else None}...")
    
    is_admin = False
    
    if token:
        try:
            # Decode the token
            payload = jwt.decode(
                token,
                app.config.get('JWT_SECRET_KEY'),
                algorithms=["HS256"]
            )
            
            # Check if user has admin role
            if payload.get('role') == 'admin':
                app.logger.info(f"Admin user detected: {payload.get('sub')}")
                is_admin = True
        except Exception as e:
            app.logger.warning(f"Invalid token, error: {str(e)}")
    
    # For testing only: admin bypass option
    # WARNING: DO NOT USE IN PRODUCTION - SECURITY RISK
    admin_bypass = False
    if request.cookies.get('admin_bypass') == 'true' or request.args.get('admin_bypass') == 'true':
        app.logger.warning("Admin bypass enabled - granting admin access (TESTING ONLY)")
        is_admin = True
        admin_bypass = True
    
    app.logger.info(f"Rendering Wellness module with is_admin={is_admin} (bypass={admin_bypass})")
    return render_template('modules/wellness_unified.html', is_admin=is_admin)

@app.route('/app/module/wellness/dashboard')
@token_required
def wellness_dashboard():
    """Serve Wellness module with unified tabs interface"""
    # First, check for admin status from URL param for testing
    if request.args.get('admin') == 'true':
        app.logger.info("Admin access granted via URL parameter (testing only)")
        return render_template('modules/wellness_unified.html', is_admin=True)
    
    # Get JWT token and check for admin role
    token = None
    
    # Try to get token from various sources
    if 'x-access-token' in request.headers:
        token = request.headers['x-access-token']
    elif 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    elif request.cookies.get('token'):
        token = request.cookies.get('token')
            
    app.logger.info(f"Wellness dashboard accessed with token: {token[:10] if token else None}...")
    
    is_admin = False
    
    if token:
        try:
            # Decode the token
            payload = jwt.decode(
                token,
                app.config.get('JWT_SECRET_KEY'),
                algorithms=["HS256"]
            )
            
            # Check if user has admin role
            if payload.get('role') == 'admin':
                app.logger.info(f"Admin user detected: {payload.get('sub')}")
                is_admin = True
        except Exception as e:
            app.logger.warning(f"Invalid token, error: {str(e)}")
    
    # For testing only: admin bypass option
    # WARNING: DO NOT USE IN PRODUCTION - SECURITY RISK
    admin_bypass = False
    if request.cookies.get('admin_bypass') == 'true' or request.args.get('admin_bypass') == 'true':
        app.logger.warning("Admin bypass enabled - granting admin access (TESTING ONLY)")
        is_admin = True
        admin_bypass = True
    
    app.logger.info(f"Rendering Wellness dashboard with is_admin={is_admin} (bypass={admin_bypass})")
    return render_template('modules/wellness_unified.html', is_admin=is_admin)
        
@app.route('/app/module/wellness/charts')
def wellness_charts_direct():
    """Direct handler for wellness charts dashboard with ApexCharts visualization"""
    # Don't enforce token for development
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/wellness_unified.html')

# Detox module routes
@app.route('/app/detox')
def detox_module():
    """Serve Detox module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/detox_unified.html')

@app.route('/app/module/wellness/detox')
def wellness_detox_module():
    """Serve Detox module within wellness"""
    return render_template('modules/detox_unified.html')

# Goal Coach module routes
@app.route('/app/goalcoach')
@app.route('/app/goal-coach')
@app.route('/app/goals')
def goalcoach_module():
    """Serve Goal Coach module"""
    admin_mode = request.args.get('admin') == 'true'
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/goalcoach_unified.html', is_admin=admin_mode)

# Environment module routes
@app.route('/app/module/environment')
def environment_module_unified():
    """Serve Environment module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/environment_unified.html', is_admin=admin_mode)

# Kitchen module routes
@app.route('/app/module/kitchen')
def kitchen_module_unified():
    """Serve Kitchen module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/kitchen_unified.html', is_admin=admin_mode)

# Wardrobe module routes
@app.route('/app/module/wardrobe')
def wardrobe_module_unified():
    """Serve Wardrobe module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/wardrobe_unified.html', is_admin=admin_mode)

# Marketplace module routes
@app.route('/app/module/marketplace')
def marketplace_module_unified():
    """Serve Marketplace module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/marketplace_unified.html', is_admin=admin_mode)

# Budget module routes
@app.route('/app/module/budget')
def budget_module_unified():
    """Serve Budget module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/budget_unified.html', is_admin=admin_mode)

# Grocery module routes
@app.route('/app/module/grocery')
def grocery_module_unified():
    """Serve Grocery module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/grocery_unified.html', is_admin=admin_mode)

# LifeCare module routes
@app.route('/app/module/lifecare')
def lifecare_module_unified():
    """Serve LifeCare module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/lifecare_unified.html', is_admin=admin_mode)

# Community module routes
@app.route('/app/module/community')
def community_module_unified():
    """Serve Community module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/community_unified.html', is_admin=admin_mode)

# Menstrual Health module routes
@app.route('/app/module/menstrual')
def menstrual_module_unified():
    """Serve Menstrual Health module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/menstrual_unified.html', is_admin=admin_mode)

# Smart Scheduler module routes
@app.route('/app/module/scheduler')
def scheduler_module_unified():
    """Serve Smart Scheduler module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/scheduler.html', is_admin=admin_mode)

# Rewards module routes
@app.route('/app/module/rewards')
def rewards_module_unified():
    """Serve Rewards module with unified interface"""
    admin_mode = request.args.get('admin') == 'true'
    return render_template('modules/rewards.html', is_admin=admin_mode)

@app.route('/app/module/goalcoach')
@app.route('/app/module/goals')
@app.route('/app/module/goalcoach/dashboard')
def goalcoach_dashboard():
    """Serve Goal Coach module with unified tabs interface"""
    return render_template('modules/goalcoach_unified.html')

# Community module routes
@app.route('/app/community')
def community_module():
    """Serve Community module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/community_unified.html')

@app.route('/app/module/community')
@app.route('/app/module/community/dashboard')
def community_dashboard():
    """Serve Community module with unified tabs interface"""
    return render_template('modules/community_unified.html')

# Menstrual Health module routes
@app.route('/app/menstrual-cycle')
@app.route('/app/menstrual')
@app.route('/app/module/menstrual')
def menstrual_module():
    """Serve Menstrual Health module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/menstrual_unified.html')

@app.route('/app/module/wellness/menstrual')
def wellness_menstrual_module():
    """Serve Menstrual Health module within wellness"""
    return render_template('modules/menstrual_unified.html')

@app.route('/app/budget-tracker')
def budget_tracker_module():
    """Serve Budget Tracker module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/budget.html')

@app.route('/app/inner-cosmos')
def inner_cosmos_module():
    """Serve Inner Cosmos module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/inner_cosmos.html')

@app.route('/app/consciousness')
def consciousness_module():
    """Serve Consciousness module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/consciousness.html')

# Handle specific profile routes
@app.route('/app/profile')
def user_profile():
    """Serve the user profile page"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        # Get user data from token
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and 'Bearer' in auth_header:
            token = auth_header.split(' ')[1]
        else:
            token = request.cookies.get('auth_token')
            
        user_data = None
        if token:
            try:
                # Use JWT decode directly
                from flask_jwt_extended import decode_token as jwt_decode_token
                decoded = jwt_decode_token(token)
                if decoded and 'sub' in decoded:
                    user_id = decoded['sub']
                    user = db.session.query(User).filter_by(uid=user_id).first()
                    if user:
                        user_data = user
            except Exception as e:
                app.logger.error(f"Error decoding token for profile page: {e}")
                
        return render_template('user/profile.html', current_user=user_data)

# Handle goals with dynamic paths
@app.route('/app/goals/<path:path>')
def user_goals(path):
    """Serve the user goals pages with path parameter"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    elif path == 'coach' or path == 'coaching':
        # Redirect to the new Goal Coach module
        from flask import redirect
        return redirect('/app/module/goalcoach')
    else:
        return render_template('user/goals.html', path=path)

# Handle common app routes without path parameters
@app.route('/app/notifications')
@app.route('/app/marketplace')
@app.route('/app/plant-ai')
@app.route('/app/grocery')
@app.route('/app/fridge-tracker')
@app.route('/app/medical-ai')
@app.route('/app/sustainability')
@app.route('/app/kitchen-ai')
@app.route('/app/sleep')
@app.route('/app/health-records')
@app.route('/app/closet-ai')
@app.route('/app/laundry-tracker')
@app.route('/app/challenge')
@app.route('/app/media')
@app.route('/app/education')
@app.route('/app/smart-eco-home')
@app.route('/app/scan-suggest')
@app.route('/app/household')
@app.route('/app/meal-planner')
@app.route('/app/waste-tracker')
@app.route('/app/module-manager')
@app.route('/app/onboarding')
@app.route('/app/help')
def serve_general_routes():
    """Serve React app for general app routes"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        # Default to hub view for simplicity
        return redirect('/app/ecosyno-hub')
        
# Add dedicated settings page route
@app.route('/app/settings')
def user_settings():
    """Serve the user settings page"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        # Get user data from token
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and 'Bearer' in auth_header:
            token = auth_header.split(' ')[1]
        else:
            token = request.cookies.get('auth_token')
            
        user_data = None
        if token:
            try:
                # Use JWT decode directly
                from flask_jwt_extended import decode_token as jwt_decode_token
                decoded = jwt_decode_token(token)
                if decoded and 'sub' in decoded:
                    user_id = decoded['sub']
                    user = db.session.query(User).filter_by(uid=user_id).first()
                    if user:
                        user_data = user
            except Exception as e:
                app.logger.error(f"Error decoding token for settings page: {e}")
                
        return render_template('user/settings.html', current_user=user_data)

# Add dedicated routes for our new modules
@app.route('/app/scheduler')
def scheduler_module():
    """Serve the Smart Scheduler module"""
    return render_template('modules/scheduler.html')

@app.route('/app/rewards')
def rewards_module():
    """Serve the Rewards module"""
    # Simple approach - always enable admin tab for testing purposes
    # In a production environment, this would check user permissions
    is_admin = True
    admin_param = request.args.get('admin')
    if admin_param == 'false':
        is_admin = False
    
    app.logger.info(f"Rendering Rewards module with is_admin={is_admin}")
    return render_template('modules/rewards.html', is_admin=is_admin)


@app.route('/app/subscription')
@token_required
def subscription_page():
    """Serve the Subscription plans and management page"""
    # Get user's current subscription tier from the database
    # For demo purposes, we'll hardcode 'basic' as the current tier
    current_tier = 'basic'
    return render_template('modules/subscription/plans.html', current_tier=current_tier)


@app.route('/app/subscription-preview')
def subscription_page_preview():
    """Serve the Subscription plans and management page (public preview)"""
    # Get user's current subscription tier from the database
    # For demo purposes, we'll hardcode 'basic' as the current tier
    current_tier = 'basic'
    return render_template('modules/subscription/plans.html', current_tier=current_tier)


@app.route('/app/integration-guide')
def integration_guide_page():
    """Serve the EcoSyno Integration Guide page"""
    return render_template('integration_guide.html')


@app.route('/api/subscription/status')
@token_required
def get_subscription_status():
    """Get the current user's subscription status"""
    # In a real app, this would fetch from the database
    # For demo purposes, we'll use localStorage on the client
    # But provide a server-side API endpoint for future use
    subscription_data = {
        'tier': 'basic',
        'features': {
            'environment': True,
            'wellness': True,
            'kitchen': True,
            'marketplace': True,
            'wardrobe': False,
            'goalcoach': False,
            'community': False,
            'budget': False,
            'grocery': False,
            'lifecare': False,
            'synomind': False,
            'detox': False,
            'menstrual': False
        },
        'expiresAt': '2025-06-14T00:00:00.000Z'
    }
    return jsonify(subscription_data)


@app.route('/api/subscription/update', methods=['POST'])
@token_required
def update_subscription():
    """Update the user's subscription tier"""
    # In a real app, this would update the database and handle payment
    data = request.get_json()
    if not data or 'tier' not in data:
        return jsonify({'error': 'Missing tier parameter'}), 400
        
    # Validate tier value
    valid_tiers = ['free', 'basic', 'standard', 'premium']
    if data['tier'] not in valid_tiers:
        return jsonify({'error': 'Invalid tier value'}), 400
        
    # For demo, we'll just acknowledge the request
    # In production, this would update the user's subscription in the database
    return jsonify({
        'success': True,
        'message': f'Subscription updated to {data["tier"]} tier',
        'tier': data['tier']
    })

# Handle routes with specific nested paths
@app.route('/app/waste-tracker/weekly-report')
@app.route('/app/onboarding/profile-setup')
@app.route('/app/help/walkthroughs')
def serve_nested_routes():
    """Serve React app for nested routes"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        # Default to dashboard view for simplicity
        return render_template('dashboard.html')

@app.route('/app/module/<path:path>')
@token_required
def serve_module_routes(path):
    """Serve React app for module-specific routes"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        # Parse the path to determine which module and section to show
        parts = path.split('/')
        module = parts[0] if parts else ""
        section = parts[1] if len(parts) > 1 else ""
        
        # Map module names to their template files
        module_templates = {
            'wellness': 'modules/wellness_unified.html',
            'environment': 'modules/environment_unified.html',
            'kitchen': 'modules/kitchen_unified.html',
            'wardrobe': 'modules/wardrobe_unified.html',
            'marketplace': 'modules/marketplace_unified.html',
            'lifecare': 'modules/lifecare_unified.html',
            'budget': 'modules/budget_unified.html',
            'grocery': 'modules/grocery_unified.html',
            'synomind': 'modules/synomind.html',
            'detox': 'modules/detox_unified.html',
            'goalcoach': 'modules/goalcoach_unified.html',
            'community': 'modules/community_unified.html',
            'menstrual': 'modules/menstrual_unified.html',
        }
        
        if module in module_templates:
            return render_template(module_templates[module], active_section=section if section else module)
        
        # Fallback to dashboard
        return redirect('/app/dashboard')

# Additional direct route handlers for specific modules that need special handling
@app.route('/app/waste-tracker')
@token_required
def waste_tracker_module_direct():
    """Direct handler for waste tracker module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/environment.html', active_section='waste-tracker')

@app.route('/app/fridge-tracker')
@token_required
def fridge_tracker_module_direct():
    """Direct handler for fridge AI module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/kitchen_unified.html')
        
@app.route('/app/laundry-tracker')
@token_required
def laundry_tracker_module_direct():
    """Direct handler for laundry tracker module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/wardrobe.html', active_section='laundry')
        
@app.route('/app/meditation')
@token_required
def meditation_module_direct():
    """Direct handler for meditation module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/wellness.html', active_section='meditation')

@app.route('/app/module/environment/plants')
@token_required
def environment_plants_direct():
    """Direct handler for environment plants module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/environment_plants.html')
        
@app.route('/app/module/environment/water')
@token_required
def environment_water_direct():
    """Direct handler for environment water module"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/environment_water.html')
        
@app.route('/app/module/environment/charts')
def environment_charts_direct():
    """Direct handler for environment charts dashboard"""
    # Don't enforce token for development
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/environment_simple.html')
        
@app.route('/app/module/environment/iot')
def environment_iot_direct():
    """Direct handler for environment IoT control center"""
    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return render_template('modules/environment_iot.html')

@app.route('/test-working')
def test_working_page():
    """Simple test page that should always work"""
    return render_template('working_test.html')
    
@app.route('/login-status')
def login_status_page():
    """Show current login status, with options to log in or out"""
    return render_template('login_status.html')

@app.route('/troubleshooter')
def system_troubleshooter():
    """System troubleshooter utility"""
    return render_template('troubleshooter.html')

@app.route('/app/dashboard-simple')
def simple_dashboard():
    """Simplified dashboard page"""
    return render_template('user_dashboard_simple.html')

@app.route('/auth/login-simple')
def simple_login():
    """Simplified login page"""
    return render_template('login_simple.html')

@app.route('/app/module/environment/charts-simple')
def environment_charts_simple():
    """Simplified environment charts page"""
    return render_template('modules/environment_charts_simple.html')

@app.route('/test-token')
def test_token_page():
    """Generate test authentication token"""
    return render_template('test_token.html')

@app.route('/direct-login')
def direct_login_page():
    """Show the direct login page with separate Admin and Super Admin buttons"""
    return render_template('direct_login.html')
    

    
@app.route('/create-admin-direct', methods=['POST'])
def create_admin_direct():
    """Create a super admin user directly with proper database references"""
    try:
        # Get data from request
        data = request.json
        email = data.get('email', 'superadmin@ecosyno.app')
        password = data.get('password', 'superadmin123')
        display_name = data.get('display_name', 'Super Admin')
        admin_level = data.get('admin_level', 'superadmin')
        
        # Create user with proper UID format
        uid = f"super:{uuid.uuid4()}"
        user = User(
            uid=uid,
            email=email,
            password=password,
            role=ROLE_SUPER_ADMIN,
            display_name=display_name
        )
        db.session.add(user)
        db.session.flush()  # Flush to get the ID without committing
        
        # Create AdminUser entry (used for admin login)
        admin_user = AdminUser(
            email=email,
            password=password,
            role=ROLE_SUPER_ADMIN
        )
        db.session.add(admin_user)
        db.session.flush()
        
        # Create Admin profile with proper user_id reference to uid (not id)
        admin_profile = Admin(
            user_id=uid,  # Correct: use uid here, not user.id
            admin_level=admin_level,
            permissions={"all": True}
        )
        db.session.add(admin_profile)
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Super Admin user created with proper database references',
            'user': {
                'uid': uid,
                'email': email,
                'role': ROLE_SUPER_ADMIN,
                'display_name': display_name
            },
            'admin': {
                'level': admin_level,
                'permissions': 'All access'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    

    
@app.route('/create-admin-token')
def create_admin_token():
    """Create an admin token and redirect to the appropriate dashboard"""
    from flask_jwt_extended import create_access_token
    from flask import make_response, request
    from models import ROLE_ADMIN, ROLE_SUPER_ADMIN
    
    # Get the role from query parameter
    role = request.args.get('role', 'admin')
    
    if role == 'superadmin':
        # Create Super Admin token
        identity = "superadmin@ecosyno.app"
        admin_role = ROLE_SUPER_ADMIN
        redirect_url = '/admin/super-admin-dashboard'
    else:
        # Create regular Admin token
        identity = "admin@ecosyno.app"
        admin_role = ROLE_ADMIN
        redirect_url = '/app/module/environment/dashboard?admin=true'
    
    # Create the token
    token = create_access_token(
        identity=identity,
        additional_claims={"role": admin_role}
    )
    
    # Create response with redirect
    response = make_response(redirect(redirect_url))
    
    # Set the token as a cookie
    response.set_cookie('access_token', token, httponly=False)
    
    # Also include JavaScript to set localStorage
    js_script = f"""
    <script>
    localStorage.setItem('access_token', '{token}');
    localStorage.setItem('user_role', '{admin_role}');
    window.location.href = '{redirect_url}';
    </script>
    """
    
    return js_script

@app.route('/direct-login/admin')
def direct_login_admin():
    """Process direct Admin login"""
    from flask_jwt_extended import create_access_token
    from models import ROLE_ADMIN
    import json
    from flask import make_response
    
    # Create admin token with admin role
    access_token = create_access_token(
        identity="admin@ecosyno.app",
        additional_claims={"role": ROLE_ADMIN}
    )
    
    # Create the response with token in cookies
    response = make_response(redirect('/app/module/environment/dashboard?admin=true'))
    response.set_cookie('access_token', access_token, httponly=False)
    
    # Also set localStorage via JavaScript
    js_code = f"""
    <script>
    localStorage.setItem('access_token', '{access_token}');
    window.location.href = '/app/module/environment/dashboard?admin=true';
    </script>
    """
    return js_code

@app.route('/direct-login/super-admin')
def direct_login_super_admin():
    """Process direct Super Admin login"""
    from flask_jwt_extended import create_access_token
    from models import ROLE_SUPER_ADMIN
    import json
    from flask import make_response
    
    # Create super admin token with superadmin role
    access_token = create_access_token(
        identity="superadmin@ecosyno.app",
        additional_claims={"role": ROLE_SUPER_ADMIN}
    )
    
    # Create the response with token in cookies
    response = make_response(redirect('/admin/super-admin-dashboard'))
    response.set_cookie('access_token', access_token, httponly=False)
    
    # Also set localStorage via JavaScript
    js_code = f"""
    <script>
    localStorage.setItem('access_token', '{access_token}');
    window.location.href = '/admin/super-admin-dashboard';
    </script>
    """
    return js_code
    
@app.route('/admin-access')
def admin_access_page():
    """Admin access control page for Super Admin creation and access"""
    return render_template('admin_access.html')
    
@app.route('/admin-access/create')
def admin_access_create():
    """Create a new Super Admin account"""
    from models import User, ROLE_SUPER_ADMIN
    import uuid
    
    try:
        # Create a Super Admin account
        super_admin_email = "superadmin@ecosyno.app"
        password = "superadmin123"
        admin = User.query.filter_by(email=super_admin_email).first()
        
        # If admin already exists, update role and password
        if admin:
            admin.role = ROLE_SUPER_ADMIN
            admin.set_password(password)
            db.session.commit()
            
            return render_template('admin_access.html', 
                                  status="success", 
                                  message="Super Admin account updated successfully!",
                                  account_info={
                                      "email": super_admin_email,
                                      "role": ROLE_SUPER_ADMIN,
                                      "password": password
                                  })
        
        # Create a new Super Admin with password directly in constructor
        # Generate a shorter UID that fits within 36 characters
        admin_uid = str(uuid.uuid4())
        new_admin = User(
            uid=admin_uid,
            email=super_admin_email,
            password=password,  # Pass password to constructor
            role=ROLE_SUPER_ADMIN,
            display_name="Super Admin"
        )
        db.session.add(new_admin)
        db.session.commit()
        
        return render_template('admin_access.html', 
                              status="success", 
                              message="New Super Admin account created successfully!",
                              account_info={
                                  "email": super_admin_email,
                                  "role": ROLE_SUPER_ADMIN,
                                  "password": password
                              })
    except Exception as e:
        return render_template('admin_access.html', 
                              status="error", 
                              message=f"Error creating Super Admin: {str(e)}")
    
@app.route('/admin-access/upgrade')
def admin_access_upgrade():
    """Upgrade existing admin to Super Admin"""
    from models import User, ROLE_SUPER_ADMIN
    
    try:
        # Update admin@ecosyno.app to Super Admin
        admin_email = "admin@ecosyno.app"
        password = "admin123"  # Keep existing password
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            admin.role = ROLE_SUPER_ADMIN
            db.session.commit()
            
            return render_template('admin_access.html', 
                                  status="success", 
                                  message=f"Admin account {admin_email} upgraded to Super Admin!",
                                  account_info={
                                      "email": admin_email,
                                      "role": ROLE_SUPER_ADMIN,
                                      "password": password
                                  })
        else:
            return render_template('admin_access.html', 
                                  status="error", 
                                  message=f"Admin account {admin_email} not found!")
    except Exception as e:
        return render_template('admin_access.html', 
                              status="error", 
                              message=f"Error upgrading admin: {str(e)}")
    
@app.route('/create-super-admin')
def create_super_admin_page():
    """Create a Super Admin account for testing"""
    import uuid
    from models import User, ROLE_SUPER_ADMIN
    
    try:
        # Check if super admin exists
        super_admin_email = "superadmin@ecosyno.app"
        admin = User.query.filter_by(email=super_admin_email).first()
        
        if admin:
            # If admin exists, make sure it has super_admin role
            admin.role = ROLE_SUPER_ADMIN
            db.session.commit()
            
            return render_template('super_admin_created.html', 
                                  email=super_admin_email, 
                                  status="updated",
                                  admin=admin)
        
        # Create new admin with role SUPER_ADMIN
        new_admin = User(
            uid=f"admin:{uuid.uuid4()}",
            email=super_admin_email,
            role=ROLE_SUPER_ADMIN,
            display_name="Super Admin"
        )
        new_admin.set_password("superadmin123")
        db.session.add(new_admin)
        db.session.commit()
        
        return render_template('super_admin_created.html', 
                              email=super_admin_email, 
                              status="created",
                              admin=new_admin)
    except Exception as e:
        return render_template('super_admin_created.html', 
                              email=super_admin_email, 
                              status="error",
                              error=str(e))

@app.route('/standalone')
def standalone_page():
    """Standalone diagnostic page"""
    return render_template('standalone.html')

@app.route('/app/module/environment')
@token_required
def environment_module():
    """Environment module with unified tabs interface"""
    # First, check for admin status from URL param for testing
    if request.args.get('admin') == 'true':
        app.logger.info("Admin access granted via URL parameter (testing only)")
        return render_template('modules/environment_unified.html', is_admin=True)
    
    # Get JWT token and check for admin role
    token = None
    
    # Try to get token from various sources
    if 'x-access-token' in request.headers:
        token = request.headers['x-access-token']
    elif 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    elif request.cookies.get('token'):
        token = request.cookies.get('token')
        
    app.logger.info(f"Environment module accessed with token: {token[:10] if token else None}...")
    
    is_admin = False
    
    if token:
        try:
            # Decode the token
            payload = jwt.decode(
                token,
                app.config.get('JWT_SECRET_KEY'),
                algorithms=["HS256"]
            )
            
            # Check if user has admin role
            if payload.get('role') == 'admin':
                app.logger.info(f"Admin user detected: {payload.get('sub')}")
                is_admin = True
        except Exception as e:
            app.logger.warning(f"Invalid token, error: {str(e)}")
    
    # For testing only: admin bypass option
    # WARNING: DO NOT USE IN PRODUCTION - SECURITY RISK
    admin_bypass = False
    if request.cookies.get('admin_bypass') == 'true' or request.args.get('admin_bypass') == 'true':
        app.logger.warning("Admin bypass enabled - granting admin access (TESTING ONLY)")
        is_admin = True
        admin_bypass = True
    
    app.logger.info(f"Rendering Environment module with is_admin={is_admin} (bypass={admin_bypass})")
    return render_template('modules/environment_unified.html', is_admin=is_admin)
    
@app.route('/app/module/kitchen')
@token_required
def kitchen_module():
    """Kitchen module with unified tabs interface"""
    # First, check for admin status from URL param for testing
    if request.args.get('admin') == 'true':
        app.logger.info("Admin access granted via URL parameter (testing only)")
        return render_template('modules/kitchen_unified.html', is_admin=True)
    
    # Force admin flag to true for development
    app.logger.info("Rendering Kitchen module with forced admin=True for development")
    return render_template('modules/kitchen_unified.html', is_admin=True)
    
    # Get JWT token and check for admin role (commented out for now)
    token = None
    
    # Try to get token from various sources
    if 'x-access-token' in request.headers:
        token = request.headers['x-access-token']
    elif 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    elif request.cookies.get('token'):
        token = request.cookies.get('token')
        
    app.logger.info(f"Kitchen module accessed with token: {token[:10] if token else None}...")
    
    is_admin = False
    
    if token:
        try:
            # Decode the token
            payload = jwt.decode(
                token,
                app.config.get('JWT_SECRET_KEY'),
                algorithms=["HS256"]
            )
            
            # Check if user has admin role
            if payload.get('role') == 'admin':
                app.logger.info(f"Admin user detected: {payload.get('sub')}")
                is_admin = True
        except Exception as e:
            app.logger.warning(f"Invalid token, error: {str(e)}")
    
    # For testing only: admin bypass option
    # WARNING: DO NOT USE IN PRODUCTION - SECURITY RISK
    admin_bypass = False
    if request.cookies.get('admin_bypass') == 'true' or request.args.get('admin_bypass') == 'true':
        app.logger.warning("Admin bypass enabled - granting admin access (TESTING ONLY)")
        is_admin = True
        admin_bypass = True
    
    app.logger.info(f"Rendering Kitchen module with is_admin={is_admin} (bypass={admin_bypass})")
    return render_template('modules/kitchen_unified.html', is_admin=is_admin)

@app.route('/app/module/marketplace')
def marketplace_module():
    """Marketplace module with unified tabs interface"""
    # First, check for admin status from URL param for testing
    if request.args.get('admin') == 'true':
        app.logger.info("Admin access granted via URL parameter (testing only)")
        return render_template('modules/marketplace_unified.html', is_admin=True)
    
    # Force admin flag to true for development
    app.logger.info("Rendering Marketplace module with forced admin=True for development")
    return render_template('modules/marketplace_unified.html', is_admin=True)
    
    # Get JWT token and check for admin role (commented out for now)
    token = None
    
    # Try to get token from various sources
    if 'x-access-token' in request.headers:
        token = request.headers['x-access-token']
    elif 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    elif request.cookies.get('token'):
        token = request.cookies.get('token')
        
    app.logger.info(f"Marketplace module accessed with token: {token[:10] if token else None}...")
    
    is_admin = False
    
    if token:
        try:
            # Decode the token
            payload = jwt.decode(
                token,
                app.config.get('JWT_SECRET_KEY'),
                algorithms=["HS256"]
            )
            
            # Check if user has admin role
            if payload.get('role') == 'admin':
                app.logger.info(f"Admin user detected: {payload.get('sub')}")
                is_admin = True
        except Exception as e:
            app.logger.warning(f"Invalid token, error: {str(e)}")
    
    # For testing only: admin bypass option
    # WARNING: DO NOT USE IN PRODUCTION - SECURITY RISK
    admin_bypass = False
    if request.cookies.get('admin_bypass') == 'true' or request.args.get('admin_bypass') == 'true':
        app.logger.warning("Admin bypass enabled - granting admin access (TESTING ONLY)")
        is_admin = True
        admin_bypass = True
    
    app.logger.info(f"Rendering Marketplace module with is_admin={is_admin} (bypass={admin_bypass})")
    return render_template('modules/marketplace_unified.html', is_admin=is_admin)
    
@app.route('/app/module/wardrobe')
@app.route('/app/module/wardrobe/<path:subpath>')
def wardrobe_module(subpath=None):
    """Wardrobe module with unified tabs interface"""
    # First, check for admin status from URL param for testing
    if request.args.get('admin') == 'true':
        app.logger.info("Admin access granted via URL parameter (testing only)")
        return render_template('modules/wardrobe_unified.html', is_admin=True)
    
    # Get JWT token and check for admin role
    token = None
    
    # Try to get token from various sources
    if 'x-access-token' in request.headers:
        token = request.headers['x-access-token']
    elif 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    elif request.cookies.get('token'):
        token = request.cookies.get('token')
        
    app.logger.info(f"Wardrobe module accessed with token: {token[:10] if token else None}...")
    
    is_admin = False
    
    if token:
        try:
            # Decode the token - using PyJWT directly
            import jwt  # Make sure this is imported
            
            # Decode the token
            payload = jwt.decode(
                token,
                app.config.get('JWT_SECRET_KEY'),
                algorithms=["HS256"]
            )
            
            # Check if user has admin role
            if payload.get('role') == 'admin':
                app.logger.info(f"Admin user detected: {payload.get('sub')}")
                is_admin = True
        except Exception as e:
            app.logger.warning(f"Invalid token, error: {str(e)}")
    
    # For testing only: admin bypass option
    # WARNING: DO NOT USE IN PRODUCTION - SECURITY RISK
    admin_bypass = False
    if request.cookies.get('admin_bypass') == 'true' or request.args.get('admin_bypass') == 'true':
        app.logger.warning("Admin bypass enabled - granting admin access (TESTING ONLY)")
        is_admin = True
        admin_bypass = True
    
    # Enable admin in development mode for testing
    if os.environ.get('FLASK_ENV') == 'development':
        is_admin = True
        admin_bypass = True
        app.logger.info("Development mode detected - enabling admin access")
    
    # Always enable admin for testing in this module
    is_admin = True
    
    app.logger.info(f"Rendering Wardrobe module with is_admin={is_admin} (bypass={admin_bypass})")
    return render_template('modules/wardrobe_unified.html', is_admin=is_admin)
    
@app.route('/app/module/lifecare')
@token_required
def lifecare_module():
    """LifeCare module with unified tabs interface"""
    return render_template('modules/lifecare_unified.html')

@app.route('/app/module/lifecare/<tab_name>')
@token_required
def lifecare_module_tab(tab_name):
    """LifeCare module with specific active tab"""
    return render_template('modules/lifecare_unified.html', active_tab=tab_name)
    
@app.route('/app/module/budget')
@token_required
def budget_module():
    """Budget module with unified tabs interface"""
    return render_template('modules/budget_unified.html')
    
@app.route('/app/module/budget/<tab_name>')
@token_required
def budget_module_tab(tab_name):
    """Budget module with specific active tab"""
    return render_template('modules/budget_unified.html', active_tab=tab_name)
    
@app.route('/app/module/grocery')
@token_required
def grocery_module():
    """Grocery module with unified tabs interface"""
    return render_template('modules/grocery_unified.html')
    
@app.route('/app/module/grocery/<tab_name>')
@token_required
def grocery_module_tab(tab_name):
    """Grocery module with specific active tab"""
    return render_template('modules/grocery_unified.html', active_tab=tab_name)

@app.route('/app/module/environment/dashboard')
def environment_dashboard():
    """Environment dashboard with ApexCharts visualization"""
    # First, check for admin status from URL param for testing
    if request.args.get('admin') == 'true':
        app.logger.info("Admin access granted via URL parameter (testing only)")
        return render_template('modules/environment_unified.html', is_admin=True)
    
    # Get JWT token and check for admin role
    token = None
    
    # Try to get token from various sources
    if request.headers.get('Authorization'):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    if not token and 'X-Access-Token' in request.headers:
        token = request.headers.get('X-Access-Token')
    
    if not token and request.cookies.get('access_token'):
        token = request.cookies.get('access_token')
    
    if not token and request.args.get('token'):
        token = request.args.get('token')
    
    app.logger.info(f"Environment module accessed with token: {token[:10] if token else 'None'}...")
    
    is_admin = False
    if token:
        try:
            # Decode the token
            from flask_jwt_extended import decode_token
            decoded = decode_token(token)
            
            # Check if admin role in claims
            if decoded and 'role' in decoded and (decoded['role'] == 'admin' or decoded['role'] == 'super_admin'):
                is_admin = True
                app.logger.info(f"Admin user detected: {decoded.get('sub', 'unknown')}")
            else:
                app.logger.info(f"Non-admin user detected, role: {decoded.get('role', 'none')}")
                
        except Exception as e:
            app.logger.error(f"Error checking admin status: {str(e)}")
    
    # For testing only: admin bypass option
    # WARNING: DO NOT USE IN PRODUCTION - SECURITY RISK
    admin_bypass = False
    if request.cookies.get('admin_bypass') == 'true' or request.args.get('admin_bypass') == 'true':
        app.logger.warning("Admin bypass enabled - granting admin access (TESTING ONLY)")
        is_admin = True
        admin_bypass = True
    
    app.logger.info(f"Rendering Environment module with is_admin={is_admin} (bypass={admin_bypass})")
    return render_template('modules/environment_unified.html', is_admin=is_admin)

@app.route('/env-charts')
def env_charts_page():
    """Environment charts page with Chart.js visualizations"""
    return render_template('env_charts.html')

@app.route('/basic')
def basic_page():
    """Absolutely minimal HTML page"""
    return render_template('basic.html')

@app.route('/environment-status')
def environment_status():
    """Show current environment status and configuration"""
    host = request.headers.get('Host', 'unknown')
    env = app.config.get('CURRENT_ENVIRONMENT', 'UNKNOWN')
    env_name = app.config.get('ENV_NAME', 'Unknown')
    env_color = app.config.get('ENV_COLOR', '#333')
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>{env_name} Environment Status</title>
    <style>
        body {{ font-family: system-ui; margin: 0; padding: 20px; background: #f8f9fa; }}
        .env-banner {{ 
            background: {env_color}; color: white; padding: 20px; 
            border-radius: 10px; margin-bottom: 20px; text-align: center;
        }}
        .status-card {{ background: white; padding: 25px; border-radius: 15px; max-width: 800px; margin: 0 auto; }}
        .btn {{ 
            display: inline-block; padding: 15px 30px; background: {env_color}; 
            color: white; text-decoration: none; border-radius: 8px; margin: 10px; 
        }}
    </style>
</head>
<body>
    <div class="env-banner">
        <h1>{env_name} Environment</h1>
        <p>Host: {host}</p>
        <p>Environment: {env}</p>
    </div>
    
    <div class="status-card">
        <h2>Environment Details</h2>
        <ul>
            <li><strong>Environment:</strong> {env}</li>
            <li><strong>Host:</strong> {host}</li>
            <li><strong>Debug Mode:</strong> {'Enabled' if env in ['QA', 'UAT'] else 'Disabled'}</li>
            <li><strong>Database:</strong> {env.lower()}_ecosyno</li>
        </ul>
        
        <h3>Access Platform</h3>
        <a href="/app/ecosyno-hub" class="btn">EcoSyno Hub</a>
        <a href="/api/synomind/chat" class="btn">SynoMind Chat</a>
        
        <h3>Available Environments</h3>
        <ul>
            <li><a href="https://qa.ecosyno.com/environment-status">QA Environment</a></li>
            <li><a href="https://uat.ecosyno.com/environment-status">UAT Environment</a></li>
            <li><a href="https://demo.ecosyno.com/environment-status">Demo Environment</a></li>
            <li><a href="https://ecosyno.com/environment-status">Production Environment</a></li>
        </ul>
    </div>
</body>
</html>
    '''

@app.route('/debug-routes')
def debug_routes_view():
    """Show all routes for debugging"""
    routes = []
    for rule in app.url_map.iter_rules():
        methods = []
        if rule.methods is not None:
            methods = [m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]
        
        routes.append({
            "rule": rule.rule,
            "endpoint": rule.endpoint,
            "methods": methods
        })
    
    # Sort routes alphabetically
    routes.sort(key=lambda x: x["rule"])
    
    from auth_middleware import PUBLIC_ROUTES
    return render_template('routes_debug.html', routes=routes, public_routes=PUBLIC_ROUTES)

@app.route('/healthcheck')
def healthcheck():
    """Health check endpoint that doesn't require database access"""
    import datetime
    import json
    
    now = datetime.datetime.now()
    response = {
        'status': 'ok',
        'message': 'API is running',
        'database_url_configured': bool(app.config.get('SQLALCHEMY_DATABASE_URI')),
        'timestamp': str(now)
    }
    
    return json.dumps(response)

# Define more routes to test database
@app.route('/api/users/create', methods=['GET'])
def create_test_user():
    """Create a test user (simplified for testing)"""
    import json
    from models import User
    import uuid
    
    try:
        # Create a test user with PIN 1234
        new_user = User(
            uid=str(uuid.uuid4()),
            pin='1234',
            role='user'
        )
        db.session.add(new_user)
        db.session.commit()
        
        return json.dumps({
            'status': 'success',
            'message': 'Test user created',
            'user_uid': new_user.uid
        })
    except Exception as e:
        logger.error(f"Error creating test user: {str(e)}")
        return json.dumps({
            'status': 'error',
            'message': f'Failed to create test user: {str(e)}'
        }), 500

@app.route('/api/users/all', methods=['GET'])
def get_all_users():
    """Get all users (testing only)"""
    import json
    
    try:
        # Import here to avoid circular imports
        from models import User
        
        users = User.query.all()
        user_list = [{
            'id': user.id,
            'uid': user.uid,
            'role': user.role,
            'created_at': str(user.created_at)
        } for user in users]
        
        return json.dumps({
            'status': 'success',
            'user_count': len(user_list),
            'users': user_list
        })
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        return json.dumps({
            'status': 'error',
            'message': f'Failed to retrieve users: {str(e)}'
        }), 500

# Create the tables
with app.app_context():
    try:
        # Import models here to avoid circular imports
        # Import all models to ensure they're registered with SQLAlchemy
        from models import (
            User, WaterQualityEntry, Plant, PlantHealthLog,
            FridgeItem, GroceryList, GroceryItem,
            ClothingItem, LaundryLog, Outfit,
            MarketplaceItem, MarketplaceOrder, MarketplaceReview,
            MoodLog
        )
        
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

# Register GitHub Integration Wizard
try:
    from api.github_integration import register_github_integration
    register_github_integration(app)
    logger.info("GitHub Integration Wizard registered successfully")
except Exception as e:
    logger.error(f"Error registering GitHub Integration: {e}")

# GitHub access routes
@app.route('/github')
@app.route('/github-access')
def github_access():
    """GitHub Integration access page"""
    return render_template('github_access.html')

@app.route('/app/admin/github-integration')
def admin_github_integration():
    """GitHub Integration for Super Admin dashboard"""
    return render_template('github_wizard.html')

@app.route('/admin/github-integration')
def admin_github_integration_alt():
    """Alternative GitHub Integration route"""
    return render_template('github_wizard.html')

# Add a catch-all route for 404 errors
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    # Check if the path starts with /app, which should be handled by React
    if request.path.startswith('/app/'):
        if os.path.exists('frontend/dist/index.html'):
            return send_from_directory('frontend/dist', 'index.html')
    
    # If it's an API request (Accept: application/json), return JSON error
    if 'application/json' in request.headers.get('Accept', ''):
        return jsonify({
            "error": "Not found",
            "message": "The requested URL was not found on the server."
        }), 404
    
    # Otherwise show HTML error page
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
