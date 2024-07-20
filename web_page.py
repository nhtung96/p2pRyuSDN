from flask import Flask, render_template, request, jsonify
import requests
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/p2p/flow_mod')
def flow_modify():
    return render_template('flow_mod.html')

@app.route('/p2p/connect')
def peer_connect():
    return render_template('peer_connect.html')

@app.route('/p2p/peer_list/<hostname>')
def peer_list(hostname):
    return render_template('peer_list.html')

@app.route('/flow_mod/<hostname>', methods=['POST'])
def flow_mod(hostname):
    data = request.json
    url = f'http://{hostname}:8080/stats/flowentry/add'
    headers = {'Content-Type': 'application/json'}
    payload = request.json

    # Construct the curl command
    curl_command = [
        'curl', '-X', 'POST', '-H', 'Content-Type: application/json', 
        '-d', str(payload), url
    ]

    try:
        # Execute the curl command
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}", 500

@app.route('/flow_mod')
def flow_mod_page():
    return render_template('flow_mod.html')

if __name__ == '__main__':
    app.run(debug=True)