"""
Real-time Training Logs API
Shows actual training processes and system output
"""

import json
import logging
import subprocess
import psutil
from datetime import datetime
from flask import Blueprint, jsonify, request
from pathlib import Path

logger = logging.getLogger(__name__)

# Create blueprint for training logs
training_logs_bp = Blueprint('training_logs', __name__, url_prefix='/api/training-logs')

@training_logs_bp.route('/real-time', methods=['GET'])
def get_real_time_logs():
    """Get real-time training logs and process information"""
    try:
        logs = []
        
        # Check if there are actual Python training processes running
        training_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                    cmdline = ' '.join(proc.info['cmdline'])
                    if any(keyword in cmdline.lower() for keyword in ['train', 'model', 'bert', 'gpt', 'clip']):
                        training_processes.append({
                            'pid': proc.info['pid'],
                            'command': cmdline,
                            'cpu_percent': proc.cpu_percent(),
                            'memory_mb': proc.memory_info().rss / 1024 / 1024
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Add current system status
        current_time = datetime.now().strftime('%H:%M:%S')
        
        if training_processes:
            logs.append({
                'timestamp': current_time,
                'level': 'SUCCESS',
                'message': f'Found {len(training_processes)} active training processes'
            })
            
            for proc in training_processes:
                logs.append({
                    'timestamp': current_time,
                    'level': 'INFO',
                    'message': f'PID {proc["pid"]}: {proc["command"][:100]}... (CPU: {proc["cpu_percent"]:.1f}%, RAM: {proc["memory_mb"]:.1f}MB)'
                })
        else:
            logs.append({
                'timestamp': current_time,
                'level': 'INFO',
                'message': 'No active training processes detected'
            })
        
        # Check GPU usage if available
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_info = result.stdout.strip().split('\n')[0].split(', ')
                logs.append({
                    'timestamp': current_time,
                    'level': 'INFO',
                    'message': f'GPU Usage: {gpu_info[0]}% | VRAM: {gpu_info[1]}MB/{gpu_info[2]}MB'
                })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logs.append({
                'timestamp': current_time,
                'level': 'WARNING',
                'message': 'GPU monitoring unavailable'
            })
        
        # Check actual training status from installation file
        installation_file = Path("models/installed/installation_status.json")
        if installation_file.exists():
            with open(installation_file, 'r') as f:
                status_data = json.load(f)
            
            active_count = status_data.get('training_status', {}).get('active_sessions', 0)
            logs.append({
                'timestamp': current_time,
                'level': 'INFO',
                'message': f'Training Status: {active_count} active sessions, last updated {status_data.get("training_status", {}).get("last_updated", "unknown")}'
            })
        
        # System resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        logs.append({
            'timestamp': current_time,
            'level': 'SYSTEM',
            'message': f'System Resources: CPU {cpu_percent}%, RAM {memory.percent}% ({memory.used//1024//1024}MB/{memory.total//1024//1024}MB)'
        })
        
        return jsonify({
            'success': True,
            'logs': logs,
            'active_processes': len(training_processes),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting training logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': [{
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'ERROR',
                'message': f'Failed to fetch training logs: {str(e)}'
            }]
        }), 500

@training_logs_bp.route('/processes', methods=['GET'])
def get_training_processes():
    """Get detailed information about running training processes"""
    try:
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'create_time']):
            try:
                if proc.info['name'] in ['python', 'python3', 'node', 'npm']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if any(keyword in cmdline.lower() for keyword in ['train', 'model', 'ai', 'synomind', 'bert', 'gpt']):
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'command': cmdline,
                            'cpu_percent': proc.cpu_percent(),
                            'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                            'runtime_seconds': datetime.now().timestamp() - proc.info['create_time'],
                            'status': proc.status()
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return jsonify({
            'success': True,
            'processes': processes,
            'total_processes': len(processes)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def register_training_logs(app):
    """Register training logs blueprint with Flask app"""
    app.register_blueprint(training_logs_bp)
    logger.info("Training logs API registered successfully")