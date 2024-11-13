import os
import subprocess
import time
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

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
    # Service 1 collects its own information
    service1_info = get_info()
    time.sleep(2)  # Add 2-second delay here

    # Service 1 fetches Service 2 information
    try:
        service2_info = requests.get('http://service2:5000/').json()
    except:
        service2_info = {'error': 'Service2 unreachable'}

    return jsonify({
        'Service1': service1_info,
        'Service2': service2_info
    })

# New route to handle stop requests
@app.route('/stop', methods=['POST'])
def stop():
    # Placeholder response for stopping containers
    # You can implement the actual stop logic here if needed
    return jsonify({"message": "Stop function triggered, but stopping is not implemented."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8199)
