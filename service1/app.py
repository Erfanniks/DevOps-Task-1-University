import os
import subprocess
from flask import Flask, jsonify
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

    # Service 1 fetches Service 2 information
    try:
        service2_info = requests.get('http://service2:5000/').json()
    except:
        service2_info = {'error': 'Service2 unreachable'}

    return jsonify({
        'Service1': service1_info,
        'Service2': service2_info
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8199)
