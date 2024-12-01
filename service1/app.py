import os
import subprocess
import time
from datetime import datetime
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Global variables
VALID_STATES = ['INIT', 'PAUSED', 'RUNNING', 'SHUTDOWN']
current_state = 'INIT'
state_log = []
last_request_time = 0
cooldown_period = 2

def log_state_change(old_state, new_state):
    """Log state transitions with timestamp."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H.%M:%S.%fZ')
    log_entry = f"{timestamp}: {old_state}->{new_state}"
    state_log.append(log_entry)

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
    global current_state
    
    if request.method == 'GET':
        return current_state, 200
    
    if request.method == 'PUT':
        new_state = request.data.decode('utf-8').strip()
        
        if new_state not in VALID_STATES:
            return "Invalid state", 400
            
        if new_state == current_state:
            return current_state, 200
            
        old_state = current_state
        current_state = new_state
        log_state_change(old_state, new_state)
        
        if new_state == 'INIT':
            # Reset everything except logs
            global last_request_time
            last_request_time = 0
        elif new_state == 'SHUTDOWN':
            # Signal for shutdown - actual shutdown handled by container orchestration
            pass
            
        return current_state, 200

@app.route('/run-log', methods=['GET'])
def get_run_log():
    """Return the state transition log."""
    return '\n'.join(state_log), 200

@app.route('/request', methods=['GET'])
def handle_request():
    """Handle request - same as index but returns plain text."""
    if current_state == 'PAUSED':
        return "Service is paused", 503
    
    if current_state != 'RUNNING':
        return "Service is not in running state", 503

    global last_request_time
    current_time = time.time()
    
    if current_time - last_request_time < cooldown_period:
        return "Service is cooling down, please try again later", 503

    last_request_time = current_time
    
    try:
        service2_info = requests.get('http://service2:5000/').json()
        return f"Service2 status: UP\nService2 IP: {service2_info.get('ip_address', 'unknown')}", 200
    except:
        return "Service2 status: DOWN", 503

@app.route('/')
def index():
    """Main endpoint for browser interface."""
    if current_state == 'PAUSED':
        return jsonify({"error": "Service is paused"}), 503
    
    if current_state != 'RUNNING':
        return jsonify({"error": "Service is not in running state"}), 503

    global last_request_time
    current_time = time.time()
    
    if current_time - last_request_time < cooldown_period:
        return jsonify({"error": "Service is cooling down, please try again later"}), 503

    last_request_time = current_time

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
    # Log initial state
    log_state_change('Initial', 'INIT')
    app.run(host='0.0.0.0', port=8199)