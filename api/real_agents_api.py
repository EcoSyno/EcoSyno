"""
Real AI Agents API for EcoSyno
Provides endpoints to interact with actual working AI agents
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from core.real_ai_agents import REAL_AGENTS, execute_agent_task, list_available_agents, get_agent

logger = logging.getLogger(__name__)

real_agents_bp = Blueprint('real_agents', __name__)

@real_agents_bp.route('/status', methods=['GET'])
def get_real_agents_status():
    """Get status of all real AI agents"""
    try:
        agents_status = {}
        
        for agent_name, agent in REAL_AGENTS.items():
            agents_status[agent_name] = {
                "name": agent.name,
                "type": agent.agent_type,
                "tasks_completed": agent.tasks_completed,
                "efficiency": agent.efficiency,
                "last_active": agent.last_active,
                "status": "active"
            }
        
        return jsonify({
            "success": True,
            "agents": agents_status,
            "total_agents": len(REAL_AGENTS),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real agents status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@real_agents_bp.route('/execute', methods=['POST'])
def execute_agent_task_endpoint():
    """Execute a real task using a specific agent"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request data required"
            }), 400
        
        agent_name = data.get('agent_name')
        task = data.get('task')
        
        if not agent_name or not task:
            return jsonify({
                "success": False,
                "error": "agent_name and task are required"
            }), 400
        
        # Execute the real task
        result = execute_agent_task(agent_name, task, **data.get('params', {}))
        
        if 'error' in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "agent_name": agent_name,
            "task": task,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error executing agent task: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@real_agents_bp.route('/analyze-code', methods=['POST'])
def analyze_code():
    """Analyze code using the real code analysis agent"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({
                "success": False,
                "error": "file_path is required"
            }), 400
        
        result = execute_agent_task('code-analysis-agent', 'analyze_file', file_path=file_path)
        
        return jsonify({
            "success": True,
            "analysis": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in code analysis: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@real_agents_bp.route('/check-database', methods=['POST'])
def check_database():
    """Check database health using real database agent"""
    try:
        result = execute_agent_task('database-maintenance-agent', 'check_health')
        
        return jsonify({
            "success": True,
            "health_check": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in database check: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@real_agents_bp.route('/security-scan', methods=['POST'])
def security_scan():
    """Perform security scan using real security agent"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({
                "success": False,
                "error": "file_path is required"
            }), 400
        
        result = execute_agent_task('security-scanner-agent', 'scan_file', file_path=file_path)
        
        return jsonify({
            "success": True,
            "security_scan": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in security scan: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@real_agents_bp.route('/ai-response', methods=['POST'])
def ai_response():
    """Generate AI response using real AI agent"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        context = data.get('context', '')
        
        if not prompt:
            return jsonify({
                "success": False,
                "error": "prompt is required"
            }), 400
        
        result = execute_agent_task('ai-response-agent', 'generate_response', 
                                  prompt=prompt, context=context)
        
        if 'error' in result:
            return jsonify({
                "success": False,
                "error": result['error'],
                "note": "AI API key may not be configured. Please provide OPENAI_API_KEY or ANTHROPIC_API_KEY."
            }), 400
        
        return jsonify({
            "success": True,
            "ai_response": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in AI response: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@real_agents_bp.route('/analyze-project', methods=['POST'])
def analyze_project():
    """Analyze project structure using real filesystem agent"""
    try:
        data = request.get_json() or {}
        path = data.get('path', '.')
        
        result = execute_agent_task('filesystem-agent', 'analyze_structure', path=path)
        
        return jsonify({
            "success": True,
            "project_analysis": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in project analysis: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@real_agents_bp.route('/available-agents', methods=['GET'])
def get_available_agents():
    """Get list of available real agents"""
    try:
        agents = []
        
        for agent_name, agent in REAL_AGENTS.items():
            agents.append({
                "name": agent_name,
                "display_name": agent.name,
                "type": agent.agent_type,
                "efficiency": agent.efficiency,
                "tasks_completed": agent.tasks_completed
            })
        
        return jsonify({
            "success": True,
            "agents": agents,
            "total_count": len(agents)
        })
        
    except Exception as e:
        logger.error(f"Error getting available agents: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def register_real_agents(app):
    """Register real agents API with Flask app"""
    app.register_blueprint(real_agents_bp, url_prefix='/api/real-agents')
    logger.info("Real AI agents API registered successfully")