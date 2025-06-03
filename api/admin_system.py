"""
EcoSyno Admin System Management
Comprehensive admin functionality for real-world application
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from auth_middleware import admin_required, super_admin_required
from models import User, db
from sqlalchemy import func, text, desc
import logging
import sys
import psutil
import datetime

logger = logging.getLogger(__name__)

admin_system_bp = Blueprint('admin_system', __name__, url_prefix='/admin')

@admin_system_bp.route('/system-administration')
@login_required
@super_admin_required
def system_administration():
    """Complete system administration dashboard"""
    try:
        # Get system information
        system_info = {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'uptime': datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time()),
            'active_connections': len(psutil.net_connections()),
            'python_version': sys.version,
            'database_status': 'Connected'
        }
        
        # Get application metrics
        total_users = User.query.count()
        # Count users with recent activity (using created_at as proxy for activity)
        active_sessions = User.query.filter(User.created_at > datetime.datetime.now() - datetime.timedelta(hours=24)).count()
        
        # Get database size and performance
        db_stats = db.session.execute(text("""
            SELECT 
                pg_size_pretty(pg_database_size(current_database())) as db_size,
                (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries
        """)).fetchone()
        
        system_metrics = {
            'total_users': total_users,
            'active_sessions': active_sessions,
            'database_size': db_stats[0] if db_stats else 'Unknown',
            'active_queries': db_stats[1] if db_stats else 0
        }
        
        return render_template('admin/system_administration.html',
                             page_title="System Administration",
                             page_description="Complete system monitoring and administration",
                             system_info=system_info,
                             system_metrics=system_metrics)
                             
    except Exception as e:
        logger.error(f"Error in system administration: {e}")
        flash(f"Error loading system data: {str(e)}", 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_system_bp.route('/user-management')
@login_required
@admin_required
def user_management():
    """Complete user management with CRUD operations"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Get paginated users
        users_query = User.query.order_by(desc(User.created_at))
        users_pagination = users_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get user statistics
        user_stats = {
            'total_users': User.query.count(),
            'admin_users': User.query.filter(User.role == 'admin').count(),
            'super_admin_users': User.query.filter(User.role == 'super_admin').count(),
            'regular_users': User.query.filter(User.role == 'user').count(),
            'active_today': User.query.filter(
                User.last_login_at > datetime.datetime.now() - datetime.timedelta(days=1)
            ).count(),
            'new_this_week': User.query.filter(
                User.created_at > datetime.datetime.now() - datetime.timedelta(days=7)
            ).count()
        }
        
        # Get role distribution
        role_distribution = db.session.execute(text("""
            SELECT role, COUNT(*) as count 
            FROM users 
            GROUP BY role 
            ORDER BY count DESC
        """)).fetchall()
        
        return render_template('admin/user_management.html',
                             page_title="User Management",
                             page_description="Manage users, roles, and permissions",
                             users=users_pagination.items,
                             pagination=users_pagination,
                             user_stats=user_stats,
                             role_distribution=role_distribution)
                             
    except Exception as e:
        logger.error(f"Error in user management: {e}")
        flash(f"Error loading user data: {str(e)}", 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_system_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user details and permissions"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            user.username = request.form.get('username', user.username)
            user.email = request.form.get('email', user.email)
            user.role = request.form.get('role', user.role)
            user.is_active = request.form.get('is_active') == 'on'
            
            db.session.commit()
            flash(f"User {user.username} updated successfully", 'success')
            return redirect(url_for('admin_system.user_management'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user: {e}")
            flash(f"Error updating user: {str(e)}", 'error')
    
    return render_template('admin/edit_user.html',
                         page_title=f"Edit User: {user.username}",
                         user=user)

@admin_system_bp.route('/module-control')
@login_required
@admin_required
def module_control():
    """Complete module control and management"""
    try:
        # Get registered blueprints from the main app
        from main import app
        blueprints = app.blueprints
        
        # Categorize modules
        system_modules = ['admin', 'auth', 'core_routes', 'api_routes']
        feature_modules = [name for name in blueprints.keys() if name not in system_modules]
        
        # Get module usage statistics
        module_usage_stats = db.session.execute(text("""
            SELECT 
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_activities
            FROM (
                SELECT user_id FROM mood_logs 
                UNION ALL 
                SELECT user_id FROM water_readings 
                UNION ALL 
                SELECT user_id FROM plant_logs 
                UNION ALL 
                SELECT user_id FROM budget_logs
            ) combined_activities
        """)).fetchone()
        
        # Module status information
        module_info = {
            'total_modules': len(blueprints),
            'system_modules': len(system_modules),
            'feature_modules': len(feature_modules),
            'active_users': module_usage_stats[0] if module_usage_stats else 0,
            'total_activities': module_usage_stats[1] if module_usage_stats else 0
        }
        
        # Get detailed module list with status
        module_details = []
        for name, blueprint in blueprints.items():
            module_details.append({
                'name': name,
                'type': 'System' if name in system_modules else 'Feature',
                'url_prefix': getattr(blueprint, 'url_prefix', '/'),
                'endpoints': len(blueprint.deferred_functions),
                'status': 'Active'
            })
        
        return render_template('admin/module_control.html',
                             page_title="Module Control",
                             page_description="Monitor and control platform modules",
                             module_info=module_info,
                             module_details=module_details,
                             system_modules=system_modules,
                             feature_modules=feature_modules)
                             
    except Exception as e:
        logger.error(f"Error in module control: {e}")
        flash(f"Error loading module data: {str(e)}", 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_system_bp.route('/analytics-dashboard')
@login_required
@admin_required
def analytics_dashboard():
    """Comprehensive analytics dashboard"""
    try:
        # User analytics
        user_analytics = {
            'total_users': User.query.count(),
            'new_users_today': User.query.filter(
                User.created_at > datetime.datetime.now() - datetime.timedelta(days=1)
            ).count(),
            'active_users_week': User.query.filter(
                User.last_login_at > datetime.datetime.now() - datetime.timedelta(days=7)
            ).count()
        }
        
        # Get user growth trend (last 30 days)
        user_growth = db.session.execute(text("""
            SELECT 
                DATE(created_at) as date, 
                COUNT(*) as new_users
            FROM users 
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)).fetchall()
        
        # Module usage analytics
        module_analytics = db.session.execute(text("""
            SELECT 
                'Mood Tracking' as module, COUNT(*) as usage_count FROM mood_logs
            UNION ALL
            SELECT 'Water Monitoring', COUNT(*) FROM water_readings
            UNION ALL  
            SELECT 'Plant Care', COUNT(*) FROM plant_logs
            UNION ALL
            SELECT 'Budget Management', COUNT(*) FROM budget_logs
            UNION ALL
            SELECT 'AI Interactions', COUNT(*) FROM synomind_prompts
        """)).fetchall()
        
        # System performance metrics
        performance_metrics = {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'response_time': 'Good'  # Could be measured from actual requests
        }
        
        return render_template('admin/analytics_dashboard.html',
                             page_title="Analytics Dashboard",
                             page_description="Comprehensive platform analytics and insights",
                             user_analytics=user_analytics,
                             user_growth=user_growth,
                             module_analytics=module_analytics,
                             performance_metrics=performance_metrics)
                             
    except Exception as e:
        logger.error(f"Error in analytics dashboard: {e}")
        flash(f"Error loading analytics data: {str(e)}", 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_system_bp.route('/financial-analytics')
@login_required
@super_admin_required
def financial_analytics():
    """Financial analytics and revenue tracking"""
    try:
        # Get budget and financial data
        financial_data = db.session.execute(text("""
            SELECT 
                COALESCE(SUM(amount), 0) as total_budget,
                COALESCE(AVG(amount), 0) as avg_transaction,
                COUNT(*) as transaction_count
            FROM budget_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        """)).fetchone()
        
        # Monthly budget trends
        monthly_trends = db.session.execute(text("""
            SELECT 
                DATE_TRUNC('month', created_at) as month,
                SUM(amount) as total,
                COUNT(*) as transactions
            FROM budget_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month
        """)).fetchall()
        
        financial_metrics = {
            'total_budget_tracked': float(financial_data[0]) if financial_data and financial_data[0] else 0,
            'average_transaction': float(financial_data[1]) if financial_data and financial_data[1] else 0,
            'transaction_count': financial_data[2] if financial_data else 0,
            'monthly_trends': [
                {
                    'month': trend[0].strftime('%Y-%m'),
                    'total': float(trend[1]),
                    'transactions': trend[2]
                } for trend in monthly_trends
            ] if monthly_trends else []
        }
        
        return render_template('admin/financial_analytics.html',
                             page_title="Financial Analytics",
                             page_description="Revenue tracking and financial insights",
                             financial_metrics=financial_metrics)
                             
    except Exception as e:
        logger.error(f"Error in financial analytics: {e}")
        flash(f"Error loading financial data: {str(e)}", 'error')
        return redirect(url_for('admin.admin_dashboard'))

# API endpoints for real-time data
@admin_system_bp.route('/api/system-stats')
@login_required
@admin_required
def api_system_stats():
    """Real-time system statistics API"""
    try:
        stats = {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'active_users': User.query.filter(
                User.last_login_at > datetime.datetime.now() - datetime.timedelta(hours=1)
            ).count(),
            'timestamp': datetime.datetime.now().isoformat()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_system_bp.route('/api/user-activity')
@login_required
@admin_required
def api_user_activity():
    """Real-time user activity API"""
    try:
        activity = db.session.execute(text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as activities
            FROM (
                SELECT created_at FROM mood_logs WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                UNION ALL
                SELECT created_at FROM water_readings WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                UNION ALL
                SELECT created_at FROM plant_logs WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                UNION ALL
                SELECT created_at FROM budget_logs WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            ) combined
            GROUP BY DATE(created_at)
            ORDER BY date
        """)).fetchall()
        
        activity_data = [
            {'date': str(row[0]), 'activities': row[1]} 
            for row in activity
        ]
        
        return jsonify(activity_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500