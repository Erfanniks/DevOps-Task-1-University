import os
import subprocess
import time
from flask import Flask, jsonify
import requests

app = Flask(__name__)

# Track the last request time
last_request_time = 0
cooldown_period = 2  # Cooldown period in seconds

def get_info():
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

@app.route('/')
def index():
    global last_request_time

    # Check if we're within the cooldown period
    current_time = time.time()
    if current_time - last_request_time < cooldown_period:
        # If within cooldown, return an error without processing
        return jsonify({"error": "Service1 is cooling down, please try again later"}), 503

    # Update the last request time
    last_request_time = current_time

    # Process the request and get information
    service1_info = get_info()

    # Fetch Service 2 information
    try:
        service2_info = requests.get('http://service2:5000/').json()
    except:
        service2_info = {'error': 'Service2 unreachable'}

    # Return the response with Service 1 and Service 2 information
    return jsonify({
        'Service1': service1_info,
        'Service2': service2_info
    })

# Route to handle stop requests
@app.route('/stop', methods=['POST'])
def stop():
    return jsonify({"message": "Stop function triggered, but stopping is not implemented."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8199)
