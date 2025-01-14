import os
import subprocess
import time
from datetime import datetime
from flask import Flask, jsonify, request
import redis

app = Flask(__name__)

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, db=0)

# Constants
VALID_STATES = ['INIT', 'PAUSED', 'RUNNING', 'SHUTDOWN']
COOLDOWN_PERIOD = 2

def get_current_state():
    """Get the current state from Redis."""
    state = redis_client.get('current_state')
    return state.decode('utf-8') if state else 'INIT'

def set_current_state(new_state):
    """Set the current state in Redis."""
    redis_client.set('current_state', new_state)

def log_state_change(old_state, new_state):
    """Log state transitions with timestamps."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    log_entry = f"{timestamp}: {old_state} -> {new_state}"
    redis_client.rpush('state_log', log_entry)

@app.route('/state', methods=['GET', 'PUT'])
def manage_state():
    """Manage system state."""
    if request.method == 'GET':
        current_state = get_current_state()
        print(f"Current state: {current_state}")
        return current_state, 200
    
    if request.method == 'PUT':
        new_state = request.data.decode('utf-8').strip()
        print(f"Received payload for state transition: {new_state}")
        
        if new_state not in VALID_STATES:
            print(f"Invalid state transition attempt: {new_state}")
            return "Invalid state", 400
        
        current_state = get_current_state()
        if new_state == current_state:
            print(f"State already set to {current_state}")
            return current_state, 200
        
        log_state_change(current_state, new_state)
        set_current_state(new_state)
        
        if new_state == 'INIT':
            redis_client.delete('last_request_time')
            redis_client.delete('request_count')
            redis_client.delete('state_log')  # Clear logs on reset
            print("State reset to INIT")
        elif new_state == 'SHUTDOWN':
            redis_client.delete('current_state')
            print("System shutdown initiated")
        
        return new_state, 200

@app.route('/run-log', methods=['GET'])
def get_run_log():
    """Fetch the state transition log."""
    logs = redis_client.lrange('state_log', 0, -1)
    return '\n'.join([log.decode('utf-8') for log in logs]), 200

@app.route('/request', methods=['GET'])
def handle_request():
    """Handle client requests."""
    current_state = get_current_state()
    print(f"Handling request in state: {current_state}")

    if current_state == 'PAUSED':
        print("Service is paused")
        return jsonify({"error": "Service is paused"}), 503

    if current_state != 'RUNNING':
        print("Service is not in running state")
        return jsonify({"error": "Service is not in running state"}), 503

    last_request = redis_client.get('last_request_time')
    current_time = time.time()

    if last_request:
        last_request_time = float(last_request)
        time_since_last_request = current_time - last_request_time
        print(f"Time since last request: {time_since_last_request} seconds")
        if time_since_last_request < COOLDOWN_PERIOD:
            cooldown_remaining = COOLDOWN_PERIOD - time_since_last_request
            return jsonify({"error": f"Service is cooling down, please try again in {cooldown_remaining:.2f} seconds"}), 503

    redis_client.set('last_request_time', current_time)
    redis_client.incr('request_count', 1)

    print("Request handled successfully")
    return jsonify({"message": "Request handled successfully"}), 200


@app.route('/stop', methods=['POST'])
def stop_service():
    """Stop all containers."""
    print("Stopping all containers...")
    os.system("docker-compose down")
    return "Containers stopped successfully", 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """Expose basic metrics."""
    try:
        request_count = int(redis_client.get('request_count') or 0)
        uptime = subprocess.getoutput("uptime -p")
        return jsonify({
            "uptime": uptime,
            "request_count": request_count,
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch metrics: {str(e)}"}), 500

if __name__ == '__main__':
    # Reset the state to INIT on startup
    print("DEBUG: Resetting state to INIT on startup")
    set_current_state('INIT')
    log_state_change('Startup', 'INIT')
    app.run(host='0.0.0.0', port=8199)
