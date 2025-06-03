import os
import logging
import datetime
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create SQLAlchemy base
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
# ProxyFix temporarily disabled to fix redirect loops
# app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Content type fix removed due to Flask compatibility issues

# Construct the database URL from the PG* environment variables
# This overrides any pre-existing DATABASE_URL environment variable
pguser = os.environ.get('PGUSER')
pgpassword = os.environ.get('PGPASSWORD')
pghost = os.environ.get('PGHOST')
pgport = os.environ.get('PGPORT')
pgdatabase = os.environ.get('PGDATABASE')

if pguser and pgpassword and pghost and pgport and pgdatabase:
    # Force using the Replit PostgreSQL connection details
    database_url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}"
    logger.info("Using Replit PostgreSQL database connection from PG variables")
else:
    # Fall back to DATABASE_URL, though this will likely be the old Supabase URL
    database_url = os.environ.get('DATABASE_URL')
    logger.warning("Missing PG environment variables, falling back to DATABASE_URL")

# Create a clean database URL without any reference to the old Supabase connection
# This is to ensure we're only using the Neon database
if pguser and pgpassword and pghost and pgport and pgdatabase:
    # Construct a clean database URL from PG variables
    clean_database_url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}"
    # Override the environment variable for other parts of the app
    os.environ['DATABASE_URL'] = clean_database_url
    database_url = clean_database_url

# Debug print first few characters to see URL type without revealing credentials
if database_url:
    url_parts = database_url.split('@')
    if len(url_parts) > 1:
        safe_prefix = url_parts[0].split(':')[0] + ':***:***@' + url_parts[1].split('/')[0]
    else:
        safe_prefix = database_url[:10] + '...'
    logger.debug(f"Database URL format: {safe_prefix}")
else:
    logger.error("DATABASE_URL environment variable is not set")

# We define these here instead of in config.py to ensure they're set before loading config
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 5,  # Smaller pool size for better management
    "max_overflow": 10,
    "connect_args": {
        "sslmode": "require",  # Required for Neon database
        "connect_timeout": 10  # Shorter timeout to fail fast
    }
}
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', os.environ.get('SESSION_SECRET'))

# Load remaining config
app.config.from_object('config.Config')

# Initialize extensions with app
db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# Define routes that don't require database
@app.route('/api')
def api_root():
    return 'EcoSyno API is running. Please use the appropriate endpoints.'
    
@app.route('/api/healthcheck')
def api_healthcheck():
    """Health check endpoint that doesn't require database access"""
    now = datetime.datetime.now()
    return jsonify({
        'status': 'ok',
        'message': 'API is running',
        'database_url_configured': bool(app.config.get('SQLALCHEMY_DATABASE_URI')),
        'timestamp': str(now)
    })

# Auth blueprint will be registered in main.py to avoid circular imports

# Set fallback mode flag initially to False
app.config['DB_FALLBACK_MODE'] = False

# Import API blueprints regardless of database connection
from api.wellness import wellness_bp
from api.environment import environment_bp
from api.kitchen import kitchen_bp
from api.wardrobe import wardrobe_bp
from api.marketplace import marketplace_bp
from api.admin import admin_bp

# Skip DB connection if SKIP_DB=1 is set (for fast startup during development)
if os.environ.get('SKIP_DB') == '1':
    logger.warning("⚠️ SKIP_DB=1 environment variable is set, skipping database initialization")
    app.config['DB_FALLBACK_MODE'] = True
    # Initialize fallback module
    import fallback
else:
    # Add timeout for database initialization
    import threading
    import signal
    
    # Function to enable fallback mode after timeout
    def enable_fallback_after_timeout(timeout=15):
        def handle_timeout(signum, frame):
            app.config['DB_FALLBACK_MODE'] = True
            logger.error("Database connection timed out after {} seconds".format(timeout))
            logger.warning("Running in DATABASE FALLBACK MODE. API endpoints will return test data.")
            # Initialize fallback module
            import fallback
        
        # Set alarm for timeout seconds
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(timeout)
    
    # Only initialize database-dependent parts if DB connection works
    try:
        # Start timeout timer
        enable_fallback_after_timeout(10)
        
        with app.app_context():
            # Import models to create tables
            import models  # noqa: F401
            
            # Test database connection
            db.engine.connect()
            logger.info("Database connection successful")
            
            # Cancel timeout alarm since connection succeeded
            signal.alarm(0)
            
            # Create tables
            db.create_all()
            
            # Database connection was successful, keep fallback mode disabled
            app.config['DB_FALLBACK_MODE'] = False
            
    except Exception as e:
        # Cancel timeout alarm
        signal.alarm(0)
        
        # Enable fallback mode - the app will run but database operations will return dummy responses
        app.config['DB_FALLBACK_MODE'] = True
        logger.error(f"Database initialization error: {str(e)}")
        logger.warning("Running in DATABASE FALLBACK MODE. API endpoints will return test data.")
        
        # Initialize fallback module
        import fallback

# Register blueprints regardless of database connection status
app.register_blueprint(wellness_bp, url_prefix='/api/wellness')
app.register_blueprint(environment_bp, url_prefix='/api/environment')
app.register_blueprint(kitchen_bp, url_prefix='/api/kitchen')
app.register_blueprint(wardrobe_bp, url_prefix='/api/wardrobe')
app.register_blueprint(marketplace_bp, url_prefix='/api/marketplace')
app.register_blueprint(admin_bp)

# Add a database error route for more detailed debugging
@app.route('/db-error')
def db_error():
    status_code = 500 if not app.config.get('DB_FALLBACK_MODE', False) else 200
    
    response = {
        'error': 'Database connection failed',
        'message': 'Please check your DATABASE_URL configuration',
        'fallback_mode': app.config.get('DB_FALLBACK_MODE', False),
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    
    # Add fallback status information if in fallback mode
    if app.config.get('DB_FALLBACK_MODE', False):
        import fallback
        response.update({
            'fallback_enabled': True,
            'test_data_available': True,
            'auth_status': 'Working with test credentials',
            'admin_login': 'admin@ecosyno.app / admin123',
            'test_user': 'Any PIN code will create a test user',
            'fallback_logs': len(fallback.fallback_data.get('logs', [])),
        })
    
    return jsonify(response), status_code
