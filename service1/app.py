import os
import subprocess
import time
from datetime import datetime
from flask import Flask, jsonify, request
import requests
import redis

app = Flask(__name__)

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, db=0)

# Constants
VALID_STATES = ['INIT', 'PAUSED', 'RUNNING', 'SHUTDOWN']
cooldown_period = 2

def get_current_state():
    """Get current state from Redis."""
    state = redis_client.get('current_state')
    return state.decode('utf-8') if state else 'INIT'

def set_current_state(new_state):
    """Set current state in Redis."""
    redis_client.set('current_state', new_state)

def log_state_change(old_state, new_state):
    """Log state transitions with timestamp in Redis."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H.%M:%S.%fZ')
    log_entry = f"{timestamp}: {old_state}->{new_state}"
    redis_client.rpush('state_log', log_entry)

def get_info():
    """Gather system information."""
    ip_address = os.popen('hostname -I').read().strip()
    processes = subprocess.getoutput("ps -ax")
    disk_space = subprocess.getoutput("df -h /")
    uptime = subprocess.getoutput("uptime -p")
    return {
        'ip_address': ip_address,
        'processes': processes,
        'disk_space': disk_space,
        'uptime': uptime
    }

@app.route('/state', methods=['GET', 'PUT'])
def manage_state():
    """Handle state management."""
    if request.method == 'GET':
        return get_current_state(), 200
    
    if request.method == 'PUT':
        new_state = request.data.decode('utf-8').strip()
        
        if new_state not in VALID_STATES:
            return "Invalid state", 400
            
        current_state = get_current_state()
        if new_state == current_state:
            return current_state, 200
            
        set_current_state(new_state)
        log_state_change(current_state, new_state)
        
        if new_state == 'INIT':
            # Reset everything except logs
            redis_client.delete('last_request_time')
        elif new_state == 'SHUTDOWN':
            # Signal for shutdown - actual shutdown handled by container orchestration
            pass
            
        return new_state, 200

@app.route('/run-log', methods=['GET'])
def get_run_log():
    """Return the state transition log."""
    logs = redis_client.lrange('state_log', 0, -1)
    return '\n'.join([log.decode('utf-8') for log in logs]), 200

@app.route('/request', methods=['GET'])
def handle_request():
    """Handle request - same as index but returns plain text."""
    current_state = get_current_state()
    
    if current_state == 'PAUSED':
        return "Service is paused", 503
    
    if current_state != 'RUNNING':
        return "Service is not in running state", 503

    last_request = redis_client.get('last_request_time')
    current_time = time.time()
    
    if last_request and (current_time - float(last_request)) < cooldown_period:
        return "Service is cooling down, please try again later", 503

    redis_client.set('last_request_time', current_time)
    
    try:
        service2_info = requests.get('http://service2:5000/').json()
        return f"Service2 status: UP\nService2 IP: {service2_info.get('ip_address', 'unknown')}", 200
    except:
        return "Service2 status: DOWN", 503

@app.route('/')
def index():
    """Main endpoint for browser interface."""
    current_state = get_current_state()
    
    if current_state == 'PAUSED':
        return jsonify({"error": "Service is paused"}), 503
    
    if current_state != 'RUNNING':
        return jsonify({"error": "Service is not in running state"}), 503

    last_request = redis_client.get('last_request_time')
    current_time = time.time()
    
    if last_request and (current_time - float(last_request)) < cooldown_period:
        return jsonify({"error": "Service is cooling down, please try again later"}), 503

    redis_client.set('last_request_time', current_time)

    # Get information from both services
    service1_info = get_info()
    try:
        service2_info = requests.get('http://service2:5000/').json()
    except:
        service2_info = {'error': 'Service2 unreachable'}

    return jsonify({
        'Service1': service1_info,
        'Service2': service2_info
    })

if __name__ == '__main__':
    # Initialize state if not exists
    if not redis_client.get('current_state'):
        set_current_state('INIT')
        log_state_change('Initial', 'INIT')
    app.run(host='0.0.0.0', port=8199)