"""
Agent Recommendations API
Provides intelligent agent recommendations based on contextual analysis
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any
from core.agent_recommendation_engine import (
    recommendation_engine, 
    ContextualRequest, 
    AgentRecommendation
)

logger = logging.getLogger(__name__)

# Create blueprint for agent recommendations
agent_recommendations_bp = Blueprint('agent_recommendations', __name__, url_prefix='/api/agent-recommendations')

@agent_recommendations_bp.route('/suggest', methods=['POST'])
def suggest_agents():
    """Get intelligent agent recommendations based on context"""
    try:
        data = request.get_json()
        
        # Create contextual request from input data
        contextual_request = ContextualRequest(
            request_type=data.get('request_type', 'general'),
            description=data.get('description', ''),
            urgency=data.get('urgency', 'medium'),
            technical_complexity=data.get('technical_complexity', 'medium'),
            business_impact=data.get('business_impact', 'medium'),
            preferred_timeline=data.get('preferred_timeline', 'standard'),
            budget_considerations=data.get('budget_considerations', 'moderate')
        )
        
        # Get recommendations
        recommendations = recommendation_engine.recommend_agents(
            contextual_request, 
            max_recommendations=int(data.get('max_recommendations', 5))
        )
        
        # Convert recommendations to JSON-serializable format
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'agent_id': rec.agent_id,
                'agent_name': rec.agent_name,
                'agent_type': rec.agent_type,
                'confidence_score': rec.confidence_score,
                'reasoning': rec.reasoning,
                'estimated_completion_time': rec.estimated_completion_time,
                'cost_savings': rec.cost_savings,
                'priority_level': rec.priority_level
            })
        
        return jsonify({
            'success': True,
            'recommendations': recommendations_data,
            'total_recommendations': len(recommendations_data),
            'context_analysis': recommendation_engine.analyze_context(contextual_request)
        })
        
    except Exception as e:
        logger.error(f"Error generating agent recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'recommendations': []
        }), 500

@agent_recommendations_bp.route('/quick-suggest', methods=['POST'])
def quick_suggest():
    """Get quick agent recommendations based on simple description"""
    try:
        data = request.get_json()
        description = data.get('description', '')
        
        if not description:
            return jsonify({
                'success': False,
                'error': 'Description is required',
                'recommendations': []
            }), 400
        
        # Get real-time recommendations
        recommendations = recommendation_engine.get_real_time_recommendations(description)
        
        # Convert to JSON format
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'agent_id': rec.agent_id,
                'agent_name': rec.agent_name,
                'agent_type': rec.agent_type,
                'confidence_score': rec.confidence_score,
                'reasoning': rec.reasoning,
                'estimated_completion_time': rec.estimated_completion_time,
                'cost_savings': rec.cost_savings,
                'priority_level': rec.priority_level
            })
        
        return jsonify({
            'success': True,
            'recommendations': recommendations_data,
            'description_analyzed': description
        })
        
    except Exception as e:
        logger.error(f"Error in quick recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'recommendations': []
        }), 500

@agent_recommendations_bp.route('/context-patterns', methods=['GET'])
def get_context_patterns():
    """Get available context patterns and domains"""
    try:
        patterns = recommendation_engine.context_patterns
        capabilities = recommendation_engine.agent_capabilities
        
        # Create summary of available patterns
        pattern_summary = {}
        for domain, agents in patterns.items():
            pattern_summary[domain] = {
                'agents': agents,
                'description': _get_domain_description(domain),
                'avg_success_rate': _calculate_avg_success_rate(agents, capabilities)
            }
        
        return jsonify({
            'success': True,
            'context_patterns': pattern_summary,
            'available_domains': list(patterns.keys())
        })
        
    except Exception as e:
        logger.error(f"Error retrieving context patterns: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@agent_recommendations_bp.route('/agent-capabilities', methods=['GET'])
def get_agent_capabilities():
    """Get detailed capabilities for all agents"""
    try:
        capabilities = recommendation_engine.agent_capabilities
        
        # Enhance capabilities with additional metadata
        enhanced_capabilities = {}
        for agent_id, caps in capabilities.items():
            enhanced_capabilities[agent_id] = {
                **caps,
                'monthly_cost_savings': '₹75L',
                'team_equivalent': '100+ members',
                'deployment_readiness': 'Production Ready'
            }
        
        return jsonify({
            'success': True,
            'agent_capabilities': enhanced_capabilities,
            'total_agents': len(enhanced_capabilities)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving agent capabilities: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@agent_recommendations_bp.route('/recommendation-stats', methods=['GET'])
def get_recommendation_stats():
    """Get statistics about recommendations and agent performance"""
    try:
        capabilities = recommendation_engine.agent_capabilities
        
        # Calculate overall statistics
        total_agents = len(capabilities)
        avg_success_rate = sum(cap['success_rate'] for cap in capabilities.values()) / total_agents
        total_cost_savings = total_agents * 75  # ₹75L per agent monthly
        
        # Group agents by complexity
        complexity_distribution = {'low': 0, 'medium': 0, 'high': 0}
        for caps in capabilities.values():
            complexity_distribution[caps['complexity_level']] += 1
        
        return jsonify({
            'success': True,
            'stats': {
                'total_agents': total_agents,
                'average_success_rate': round(avg_success_rate, 1),
                'total_monthly_savings': f'₹{total_cost_savings}L',
                'total_annual_savings': f'₹{total_cost_savings * 12}L',
                'complexity_distribution': complexity_distribution,
                'domains_covered': len(recommendation_engine.context_patterns)
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating recommendation stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _get_domain_description(domain: str) -> str:
    """Get human-readable description for domain"""
    descriptions = {
        'development': 'Software development, coding, and quality assurance tasks',
        'security': 'Security audits, vulnerability scanning, and compliance checks',
        'performance': 'System optimization, monitoring, and scaling operations',
        'data': 'Data analysis, machine learning, and database management',
        'operations': 'Deployment automation, workflow management, and system operations',
        'user_facing': 'User experience optimization, interface design, and customer support'
    }
    return descriptions.get(domain, 'General purpose operations')

def _calculate_avg_success_rate(agents: list, capabilities: dict) -> float:
    """Calculate average success rate for a group of agents"""
    if not agents:
        return 0.0
    
    total_rate = sum(capabilities.get(agent, {}).get('success_rate', 0) for agent in agents)
    return round(total_rate / len(agents), 1)

# Register the blueprint
def register_agent_recommendations_api(app):
    """Register agent recommendations API with Flask app"""
    app.register_blueprint(agent_recommendations_bp)
    logger.info("Agent Recommendations API registered successfully")