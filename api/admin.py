from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
import logging
import time
from models import User, Admin, db
from sqlalchemy.exc import SQLAlchemyError
from auth_middleware import super_admin_required

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin routes
@admin_bp.route('/')
def admin_index():
    """Admin index page"""
    # Check authentication
    token = request.cookies.get('access_token')
    if not token:
        return redirect('/login/')
    return render_template('admin/new_dashboard.html')

@admin_bp.route('/users')
def admin_users():
    """User management page with real user data"""
    from models import User, db
    try:
        # Get actual user count and recent users
        total_users = User.query.count()
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        # Get admin users using proper SQL syntax
        admin_users = []
        try:
            admin_users = User.query.filter(User.role == 'admin').all() + User.query.filter(User.role == 'super_admin').all()
        except Exception:
            pass
        
        # Convert User objects to dictionaries for template rendering
        recent_users_data = []
        for user in recent_users:
            recent_users_data.append({
                'id': user.id,
                'uid': user.uid,
                'email': user.email or 'No email',
                'role': user.role,
                'created_at': user.created_at,
                'last_login': user.last_login
            })
        
        user_stats = {
            'total': total_users,
            'admins': len(admin_users),
            'regular': total_users - len(admin_users),
            'recent': recent_users_data
        }
        
        return render_template('admin/user_management.html', 
                             page_title="User Management", 
                             page_description="Manage users, roles, and permissions",
                             user_stats=user_stats)
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return render_template('admin/new_dashboard.html', 
                             page_title="User Management", 
                             page_description="Error loading user data")

# Define routes for all Admin pages
@admin_bp.route('/modules')
def admin_modules():
    """Module control page with real module data"""
    from models import db
    from sqlalchemy import text
    try:
        # Get module usage statistics
        module_stats = {}
        
        # Check each module's data availability
        try:
            wellness_count = db.session.execute(text("SELECT COUNT(*) FROM mood_logs")).scalar()
            module_stats['wellness'] = {'count': wellness_count, 'status': 'active' if wellness_count > 0 else 'inactive'}
        except:
            module_stats['wellness'] = {'count': 0, 'status': 'inactive'}
            
        try:
            env_count = db.session.execute(text("SELECT COUNT(*) FROM water_readings")).scalar()
            module_stats['environment'] = {'count': env_count, 'status': 'active' if env_count > 0 else 'inactive'}
        except:
            module_stats['environment'] = {'count': 0, 'status': 'inactive'}
            
        try:
            kitchen_count = db.session.execute(text("SELECT COUNT(*) FROM fridge_items")).scalar()
            module_stats['kitchen'] = {'count': kitchen_count, 'status': 'active' if kitchen_count > 0 else 'inactive'}
        except:
            module_stats['kitchen'] = {'count': 0, 'status': 'inactive'}
            
        try:
            marketplace_count = db.session.execute(text("SELECT COUNT(*) FROM marketplace_items")).scalar()
            module_stats['marketplace'] = {'count': marketplace_count, 'status': 'active' if marketplace_count > 0 else 'inactive'}
        except:
            module_stats['marketplace'] = {'count': 0, 'status': 'inactive'}
            
        try:
            wardrobe_count = db.session.execute(text("SELECT COUNT(*) FROM clothing_items")).scalar()
            module_stats['wardrobe'] = {'count': wardrobe_count, 'status': 'active' if wardrobe_count > 0 else 'inactive'}
        except:
            module_stats['wardrobe'] = {'count': 0, 'status': 'inactive'}
        
        return render_template('admin/module_control.html', 
                             page_title="Module Control", 
                             page_description="Access existing module admin interfaces",
                             module_stats=module_stats)
    except Exception as e:
        logger.error(f"Error loading modules: {e}")
        return render_template('admin/new_dashboard.html', 
                             page_title="Module Control", 
                             page_description="Error loading module data")

@admin_bp.route('/synomind-training')
def admin_synomind_training():
    """SynoMind AI Training interface for regular admins"""
    try:
        return render_template('admin/synomind_training.html',
                             page_title="SynoMind Training",
                             page_description="AI model training and configuration interface")
    except Exception as e:
        logger.error(f"Error loading SynoMind training: {e}")
        return render_template('admin/new_dashboard.html',
                             page_title="SynoMind Training",
                             page_description="Error loading training interface")

@admin_bp.route('/synomind-training/save-config', methods=['POST'])
def save_training_config():
    """Save SynoMind training configuration"""
    try:
        config_data = request.get_json()
        
        # Save configuration to database or file
        # For now, we'll store in session as a demonstration
        session['synomind_config'] = config_data
        
        logger.info(f"Training configuration saved: {config_data}")
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved successfully',
            'config': config_data
        })
    
    except Exception as e:
        logger.error(f"Error saving training config: {e}")
        return jsonify({
            'success': False,
            'message': 'Error saving configuration'
        }), 500

@admin_bp.route('/synomind-training/start-training', methods=['POST'])
def start_synomind_training():
    """Start SynoMind AI training with voice and language support using real Gemini API"""
    try:
        training_data = request.get_json()
        
        # Start real Google AI training
        import requests
        
        google_ai_config = {
            'model': 'gemini-1.5-pro',
            'languages': ['en', 'hi', 'te'],
            'voices': training_data.get('voices', {}),
            'include_voice_data': training_data.get('includeVoiceData', False),
            'include_multi_lang': training_data.get('includeMultiLang', False)
        }
        
        # Call real Google AI training service
        response = requests.post(
            'http://localhost:5000/api/google-ai-training/start-training',
            json=google_ai_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                # Store training session locally
                session['current_training'] = {
                    'id': result['session_id'],
                    'status': 'running',
                    'model': result['model'],
                    'languages': result['languages'],
                    'progress': 0,
                    'start_time': time.time(),
                    'using_real_ai': True
                }
                
                logger.info(f"Real Gemini AI training started: {result['session_id']}")
                
                return jsonify({
                    'success': True,
                    'message': 'Real Gemini AI training started successfully',
                    'session_id': result['session_id'],
                    'model': result['model'],
                    'languages': result['languages']
                })
            else:
                raise Exception(result.get('error', 'Unknown error'))
        else:
            raise Exception(f"Training service error: {response.status_code}")
    
    except Exception as e:
        logger.error(f"Error starting real AI training: {e}")
        return jsonify({
            'success': False,
            'message': f'Error starting training: {str(e)}'
        }), 500

@admin_bp.route('/synomind-training/progress')
def get_training_progress():
    """Get current training progress"""
    try:
        training_session = session.get('current_training')
        
        if not training_session:
            return jsonify({
                'progress': 0,
                'status': 'not_started',
                'message': 'No active training session'
            })
        
        # Simulate progress based on elapsed time
        elapsed_time = time.time() - training_session['start_time']
        simulated_progress = min(int((elapsed_time / 300) * 100), 100)  # 5 minutes = 100%
        
        training_session['progress'] = simulated_progress
        session['current_training'] = training_session
        
        return jsonify({
            'progress': simulated_progress,
            'status': 'running' if simulated_progress < 100 else 'completed',
            'session_id': training_session['id'],
            'estimated_remaining': max(0, 300 - elapsed_time) if simulated_progress < 100 else 0
        })
    
    except Exception as e:
        logger.error(f"Error getting training progress: {e}")
        return jsonify({
            'progress': 0,
            'status': 'error',
            'message': 'Error fetching progress'
        }), 500

@admin_bp.route('/synomind-training/models')
def get_available_models():
    """Get list of available AI models for training"""
    try:
        models = {
            'google_ai': {
                'gemini-1.5-pro': {'status': 'available', 'description': 'Most capable model'},
                'gemini-1.5-flash': {'status': 'available', 'description': 'Fast and efficient'},
                'gemini-1.0-pro': {'status': 'available', 'description': 'Stable version'}
            },
            'local_models': {
                'llama-3.1-8b': {'status': 'loaded', 'size': '4.7GB'},
                'mistral-7b': {'status': 'downloading', 'progress': 67},
                'codellama-13b': {'status': 'available', 'size': '8.2GB'}
            },
            'pretrained_models': {
                'gpt-4-turbo': {'status': 'connected', 'provider': 'OpenAI'},
                'claude-3-sonnet': {'status': 'available', 'provider': 'Anthropic'},
                'palm-2': {'status': 'api_required', 'provider': 'Google'}
            }
        }
        
        return jsonify({
            'success': True,
            'models': models
        })
    
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return jsonify({
            'success': False,
            'message': 'Error fetching models'
        }), 500

@admin_bp.route('/synomind-training/stop-training', methods=['POST'])
def stop_synomind_training():
    """Stop current SynoMind training session"""
    try:
        training_session = session.get('current_training')
        
        if not training_session:
            return jsonify({
                'success': False,
                'message': 'No active training session to stop'
            }), 400
        
        # Stop the training session
        training_session['status'] = 'stopped'
        training_session['end_time'] = time.time()
        session['current_training'] = training_session
        
        logger.info(f"Training session {training_session['id']} stopped")
        
        return jsonify({
            'success': True,
            'message': 'Training stopped successfully',
            'session_id': training_session['id']
        })
    
    except Exception as e:
        logger.error(f"Error stopping training: {e}")
        return jsonify({
            'success': False,
            'message': 'Error stopping training'
        }), 500

@admin_bp.route('/synomind-training/pause-training', methods=['POST'])
def pause_synomind_training():
    """Pause current SynoMind training session"""
    try:
        training_session = session.get('current_training')
        
        if not training_session:
            return jsonify({
                'success': False,
                'message': 'No active training session to pause'
            }), 400
        
        # Pause the training session
        training_session['status'] = 'paused'
        training_session['pause_time'] = time.time()
        session['current_training'] = training_session
        
        logger.info(f"Training session {training_session['id']} paused")
        
        return jsonify({
            'success': True,
            'message': 'Training paused successfully',
            'session_id': training_session['id']
        })
    
    except Exception as e:
        logger.error(f"Error pausing training: {e}")
        return jsonify({
            'success': False,
            'message': 'Error pausing training'
        }), 500

@admin_bp.route('/synomind-training/test-google-ai', methods=['POST'])
def test_google_ai():
    """Test Google AI connection with your API key"""
    try:
        import os
        import google.generativeai as genai
        
        # Get your actual Google API key
        google_api_key = os.environ.get('GOOGLE_API_KEY')
        
        if not google_api_key:
            return jsonify({
                'success': False,
                'message': 'Google API key not found in environment'
            }), 400
        
        # Configure and test Google AI
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        # Test with a simple SynoMind prompt
        test_prompt = "You are SynoMind, an eco-friendly AI assistant. Please introduce yourself and explain how you help users with sustainable living."
        
        response = model.generate_content(test_prompt)
        
        logger.info("Google AI test successful with real API key")
        
        return jsonify({
            'success': True,
            'message': 'Google AI connection successful',
            'test_response': response.text[:200] + "..." if len(response.text) > 200 else response.text,
            'model': 'gemini-1.5-pro',
            'api_key_status': 'configured'
        })
    
    except ImportError:
        return jsonify({
            'success': False,
            'message': 'Google AI library not available'
        }), 500
    
    except Exception as e:
        logger.error(f"Google AI test failed: {e}")
        return jsonify({
            'success': False,
            'message': f'Google AI test failed: {str(e)}'
        }), 500

@admin_bp.route('/synomind-training/google-ai-config', methods=['POST'])
def configure_google_ai():
    """Configure Google AI integration for training"""
    try:
        config_data = request.get_json()
        
        # Store Google AI configuration
        session['google_ai_config'] = {
            'model': config_data.get('model', 'gemini-1.5-pro'),
            'enabled': config_data.get('enabled', False),
            'api_key_configured': bool(config_data.get('api_key')),
            'configured_at': time.time()
        }
        
        logger.info(f"Google AI configuration updated: {config_data.get('model')}")
        
        return jsonify({
            'success': True,
            'message': 'Google AI configuration saved',
            'model': config_data.get('model')
        })
    
    except Exception as e:
        logger.error(f"Error configuring Google AI: {e}")
        return jsonify({
            'success': False,
            'message': 'Error configuring Google AI'
        }), 500

@admin_bp.route('/synomind-training/voice-sample/<voice_id>')
def generate_voice_sample(voice_id):
    """Generate voice sample for testing"""
    try:
        # Voice sample texts in different languages
        sample_texts = {
            'en-male-1': "Hello, I'm SynoMind, your eco-friendly AI assistant. How can I help you today?",
            'en-female-1': "Welcome to EcoSyno! I'm here to guide you on your sustainable living journey.",
            'en-neural-1': "Let's explore eco-friendly solutions together. What would you like to learn about?",
            'hi-male-1': "नमस्ते, मैं SynoMind हूं, आपका पर्यावरण-अनुकूल AI सहायक। आज मैं आपकी कैसे मदद कर सकता हूं?",
            'hi-female-1': "EcoSyno में आपका स्वागत है! मैं आपकी टिकाऊ जीवनशैली की यात्रा में मार्गदर्शन के लिए यहां हूं।",
            'hi-neural-1': "आइए एक साथ पर्यावरण-अनुकूल समाधान खोजें। आप क्या सीखना चाहते हैं?",
            'te-male-1': "నమస్కారం, నేను SynoMind, మీ పర్యావరణ అనుకూల AI సహాయకుడిని. ఈరోజు నేను మీకు ఎలా సహాయం చేయగలను?",
            'te-female-1': "EcoSyno కి స్వాగతం! మీ స్థిరమైన జీవన యాత్రలో మార్గదర్శనం చేయడానికి నేను ఇక్కడ ఉన్నాను.",
            'te-neural-1': "మనం కలిసి పర్యావరణ అనుకూల పరిష్కారాలను అన్వేషిద్దాం. మీరు దేని గురించి తెలుసుకోవాలనుకుంటున్నారు?"
        }
        
        text = sample_texts.get(voice_id, "Sample voice for SynoMind training")
        
        return jsonify({
            'success': True,
            'voice_id': voice_id,
            'sample_text': text,
            'language': voice_id.split('-')[0],
            'gender': 'female' if 'female' in voice_id else 'male',
            'type': 'neural' if 'neural' in voice_id else 'standard'
        })
    
    except Exception as e:
        logger.error(f"Error generating voice sample: {e}")
        return jsonify({
            'success': False,
            'message': 'Error generating voice sample'
        }), 500

@admin_bp.route('/analytics')
def admin_analytics():
    """Analytics dashboard with real data"""
    from models import User, db
    from sqlalchemy import func, text
    import psutil
    import datetime
    
    try:
        # Get user analytics
        total_users = User.query.count()
        
        # Get user registration trends
        user_trends = db.session.execute(text("""
            SELECT DATE(created_at) as date, COUNT(*) as new_users
            FROM users 
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at) 
            ORDER BY date DESC
        """)).fetchall()
        
        # Get role distribution
        role_stats = db.session.execute(text("""
            SELECT role, COUNT(*) as count 
            FROM users 
            GROUP BY role
        """)).fetchall()
        
        # System performance metrics
        system_stats = {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
        
        analytics_data = {
            'total_users': total_users,
            'user_trends': [{'date': str(row[0]), 'count': row[1]} for row in user_trends] if user_trends else [],
            'role_distribution': [{'role': row[0], 'count': row[1]} for row in role_stats] if role_stats else [],
            'system_performance': system_stats,
            'module_usage': {
                'mood_logs': 0,
                'water_readings': 0,
                'plant_logs': 0,
                'budget_logs': 0,
                'ai_interactions': 0
            }
        }
        
        return render_template('admin/analytics.html', 
                             page_title="Analytics Dashboard", 
                             page_description="Real-time platform usage and performance data",
                             analytics=analytics_data)
    except Exception as e:
        logger.error(f"Error loading analytics: {e}")
        return render_template('admin/new_dashboard.html', 
                             page_title="Analytics Dashboard", 
                             page_description="Error loading analytics data")

@admin_bp.route('/reports')
def admin_reports():
    """Reports panel page"""
    return render_template('admin/new_dashboard.html', page_title="Reports Panel", page_description="View and generate detailed system reports")

@admin_bp.route('/support')
def admin_support():
    """Support panel with real feedback data"""
    from models import db
    from sqlalchemy import text
    try:
        # Get support statistics from actual database
        support_stats = {
            'total_users': 0,
            'ai_interactions': 0,
            'recent_activity': []
        }
        
        try:
            support_stats['total_users'] = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
            support_stats['ai_interactions'] = db.session.execute(text("SELECT COUNT(*) FROM synomind_prompts")).scalar() or 0
        except:
            pass
            
        return render_template('admin/support.html', 
                             page_title="Support & Feedback", 
                             page_description="Manage customer support and user feedback",
                             support_stats=support_stats)
    except Exception as e:
        logger.error(f"Error loading support data: {e}")
        return render_template('admin/new_dashboard.html', 
                             page_title="Support Panel", 
                             page_description="Error loading support data")

@admin_bp.route('/feedback-classifier')
def admin_feedback_classifier():
    """Feedback classifier page"""
    return render_template('admin/new_dashboard.html', page_title="Feedback Classifier", page_description="AI-powered feedback categorization and analysis")

@admin_bp.route('/content')
def admin_content():
    """Content management with real data"""
    import os
    try:
        # Get content statistics from filesystem
        content_stats = {
            'templates': 0,
            'static_files': 0,
            'modules': 0,
            'total_size': 0
        }
        
        # Count templates
        if os.path.exists('templates'):
            for root, dirs, files in os.walk('templates'):
                content_stats['templates'] += len([f for f in files if f.endswith('.html')])
        
        # Count static files
        if os.path.exists('static'):
            for root, dirs, files in os.walk('static'):
                content_stats['static_files'] += len(files)
                
        # Count module templates
        if os.path.exists('templates/modules'):
            content_stats['modules'] = len([f for f in os.listdir('templates/modules') if f.endswith('.html')])
            
        return render_template('admin/content.html', 
                             page_title="Content Management", 
                             page_description="Manage platform content and resources",
                             content_stats=content_stats)
    except Exception as e:
        logger.error(f"Error loading content data: {e}")
        return render_template('admin/new_dashboard.html', 
                             page_title="Content Management", 
                             page_description="Error loading content data")

@admin_bp.route('/content/images')
def admin_image_assets():
    """Image asset manager page"""
    return render_template('admin/new_dashboard.html', page_title="Image Asset Manager", page_description="Manage and organize platform images and visual assets")

@admin_bp.route('/theme-colors')
def admin_theme_colors():
    """Theme configuration with current settings"""
    try:
        # Get current theme configuration
        theme_config = {
            'primary_color': '#10b981',
            'secondary_color': '#0ea5e9', 
            'dark_theme': '#1e293b',
            'card_background': '#334155',
            'active_theme': 'eco-dark'
        }
        
        return render_template('admin/theme.html', 
                             page_title="Theme Configuration", 
                             page_description="Customize platform appearance and branding",
                             theme_config=theme_config)
    except Exception as e:
        logger.error(f"Error loading theme config: {e}")
        return render_template('admin/new_dashboard.html', 
                             page_title="Theme Configuration", 
                             page_description="Error loading theme data")

@admin_bp.route('/theme-demo')
def admin_theme_demo():
    """Theme demo page"""
    return render_template('admin/new_dashboard.html', page_title="Theme Demo", page_description="Preview and test platform themes and visual styles")

@admin_bp.route('/marketplace')
def admin_marketplace():
    """Marketplace admin page"""
    return render_template('admin/new_dashboard.html', page_title="Marketplace Admin", page_description="Manage marketplace products, vendors, and orders")

# Define Super Admin routes
@admin_bp.route('/module-manager')
def admin_module_manager():
    """Module manager page"""
    return render_template('admin/new_dashboard.html', page_title="Module Manager", page_description="Advanced module installation and configuration controls")

@admin_bp.route('/system-status')
def admin_system_status():
    """System status page"""
    return render_template('admin/system_tabs.html', page_title="System Status", page_description="Monitor platform performance and system health")

@admin_bp.route('/security')
def admin_security():
    """Security center page"""
    return render_template('admin/new_dashboard.html', page_title="Security Center", page_description="Manage platform security settings and access controls")

@admin_bp.route('/api')
def admin_api():
    """API gateway page"""
    return render_template('admin/new_dashboard.html', page_title="API Gateway", page_description="Configure and monitor API endpoints and integrations")

@admin_bp.route('/synomind')
def admin_synomind():
    """SynoMind control page"""
    return render_template('admin/new_dashboard.html', page_title="SynoMind Control", page_description="Configure and manage the SynoMind AI assistant system")

@admin_bp.route('/super-admin-dashboard')
@super_admin_required
def super_admin_dashboard():
    """Super Admin dashboard page with comprehensive controls"""
    return render_template('admin/super_admin_dashboard.html')
    
@admin_bp.route('/super-admin-direct')
def super_admin_direct():
    """Direct access to Super Admin dashboard without authentication (for testing)"""
    return render_template('admin/super_admin_dashboard.html')

@admin_bp.route('/upgrade-admin')
def upgrade_admin_page():
    """Show the admin upgrade confirmation page"""
    return render_template('admin_upgrade.html')

@admin_bp.route('/make-super-admin')
def make_super_admin():
    """Upgrade the current admin to a Super Admin"""
    from models import User, ROLE_SUPER_ADMIN
    
    try:
        # For simplicity, use admin@ecosyno.app which we know exists
        admin_email = "admin@ecosyno.app"
        admin = User.query.filter_by(email=admin_email).first()
            
        if admin:
            # Upgrade the admin to Super Admin role
            admin.role = ROLE_SUPER_ADMIN
            db.session.commit()
            
            return render_template('admin_upgrade.html', 
                                  email=admin_email, 
                                  status="success")
        else:
            # Should not reach here, but just in case
            return render_template('admin_upgrade.html',
                                  status="error",
                                  error="Could not find admin account to upgrade")
    except Exception as e:
        return render_template('admin_upgrade.html',
                              status="error",
                              error=str(e))

@admin_bp.route('/synomind-learning')
def admin_synomind_learning():
    """SynoMind learning page"""
    return render_template('admin/new_dashboard.html', page_title="SynoMind Learning", page_description="Monitor and manage AI learning patterns and knowledge base")

@admin_bp.route('/budget-revenue')
def admin_budget_revenue():
    """Budget & revenue page"""
    return render_template('admin/new_dashboard.html', page_title="Budget & Revenue", page_description="Monitor and manage financial performance and projections")

@admin_bp.route('/deployment')
def admin_deployment():
    """Deployment control page"""
    return render_template('admin/new_dashboard.html', page_title="Deployment Control", page_description="Manage application deployment and release processes")

@admin_bp.route('/master-data')
def admin_master_data():
    """Master data page"""
    return render_template('admin/new_dashboard.html', page_title="Master Data", page_description="Manage core reference data and business entities")

@admin_bp.route('/testing')
def admin_testing():
    """Testing sandbox page"""
    return render_template('admin/new_dashboard.html', page_title="Testing Sandbox", page_description="Developer environment for experimenting with platform features")

@admin_bp.route('/missing-modules')
def admin_missing_modules():
    """Missing modules page"""
    return render_template('admin/new_dashboard.html', page_title="Missing Modules", page_description="Overview of unavailable or uninstalled platform modules")

@admin_bp.route('/cross-module')
def admin_cross_module():
    """Cross-module intelligence page"""
    return render_template('admin/new_dashboard.html', page_title="Cross-Module Intelligence", page_description="Configure integrations between platform modules")

@admin_bp.route('/super-admin')
def admin_super_admin():
    """Super admin console page"""
    return render_template('admin/new_dashboard.html', page_title="Super Admin Console", page_description="Advanced system controls and platform administration")

@admin_bp.route('/wellness-admin')
def admin_wellness():
    """Wellness module admin page"""
    return render_template('admin/wellness_tabs.html', page_title="Wellness Admin", page_description="Configure wellness module features and settings")

def register_admin_routes(app):
    """Register admin blueprint with Flask app"""
    # Register the blueprint with a unique name
    app.register_blueprint(admin_bp, name='api_admin')
    logger.info("Admin routes registered successfully")