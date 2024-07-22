from flask import Flask, render_template, request, jsonify, Response, redirect
import requests
import subprocess
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/p2p/flow_mod')
def flow_modify():
    return render_template('flow_mod.html')

@app.route('/p2p/connect')
def peer_connect():
    return render_template('peer_connect.html')

@app.route('/p2p/connect/<hostname1>/<hostname2>', methods=['GET'])
def peer_connect_by_hostname(hostname1, hostname2):
    try:
        # Construct the URL to fetch peer list from the specified hostname
        url = f'http://{hostname1}:8080/p2p/join/{hostname2}'
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        return jsonify(response.json())  # Return the JSON response from the other server
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/p2p/peer_list', methods=['GET'])
def peer_list_page():
    return render_template('peer_list.html')

@app.route('/p2p/peer_list/<hostname>', methods=['GET'])
def peer_list_by_hostname(hostname):
    try:
        # Construct the URL to fetch peer list from the specified hostname
        url = f'http://{hostname}:8080/p2p/peer_list'
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        return jsonify(response.json())  # Return the JSON response from the other server
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

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
    
@app.route('/p2p/flow_table', methods=['GET'])
def flow_table_page():
    return render_template('flow_table.html')

@app.route('/p2p/flow_table/<hostname>', methods=['GET'])
def flow_table_by_hostname(hostname):
    try:
        # Construct the URL to fetch flow table from the specified hostname
        url = f'http://{hostname}:8080/p2p/global/flows'
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        return jsonify(response.json())  # Return the JSON response from the other server
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/p2p/topology', methods=['GET'])
def topology_page():
    return render_template('topology.html')

@app.route('/p2p/topology/<hostname>', methods=['GET'])
def proxy_topology(hostname):
    try:
        # Construct the URL to fetch the webpage from the specified hostname
        url = f'http://{hostname}:8080/p2p/global/topology'
        
        # Forward the request to the target server
        response = requests.get(url, headers=request.headers, stream=True)
        response.raise_for_status()  # Check for HTTP errors
        
        # Create a new response with the content from the target server
        return Response(
            response.iter_content(chunk_size=1024),
            content_type=response.headers.get('Content-Type'),
            status=response.status_code
        )
    except requests.RequestException as e:
        return str(e), 500
    

@app.route('/p2p/topology/local', methods=['GET'])
def topology_page_local():
    return render_template('topology_local_load.html')

@app.route('/p2p/topology/local/<hostname>', methods=['GET'])
def proxy_topology_local(hostname):
    try:
        # Construct the URL to fetch the webpage from the specified hostname
        url = f'http://{hostname}:8080/p2p/topology'
        
        # Forward the request to the target server
        response = requests.get(url, headers=request.headers, stream=True)
        response.raise_for_status()  # Check for HTTP errors
        
        # Create a new response with the content from the target server
        return Response(
            response.iter_content(chunk_size=1024),
            content_type=response.headers.get('Content-Type'),
            status=response.status_code
        )
    except requests.RequestException as e:
        return str(e), 500
    
@app.route('/p2p/topology/gui', methods=['GET', 'POST'])
def topology_gui():
    if request.method == 'POST':
        hostname = request.form.get('hostname')
        if hostname:
            return redirect(f'http://{hostname}:8080')
    return render_template('topology_gui.html')

if __name__ == '__main__':
    app.run(debug=True)