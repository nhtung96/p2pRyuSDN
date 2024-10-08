from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import Response
from ryu.app.wsgi import route
from ryu.app.wsgi import WSGIApplication
from ryu.base import app_manager

from cryptography.hazmat.backends import default_backend
import os
import base64
import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import hashlib

import re
import json
import ast

import socket

from pymongo import MongoClient
import os

test_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Ryu Application</title>
</head>
<body>
    <h1>Welcome to the Ryu Application</h1>
    <p>This is a simple web page served by the Ryu application.</p>
</body>
</html>
"""

hostname = socket.gethostname()  # Change this to "hostnameB" for the other node
public_key_path = "/home/huutung/.ssh/id_rsa.pub.pem"  # Change this to "public_key_B.pem" for the other node
private_key_path = "/home/huutung/.ssh/id_rsa"  # Change this to "private_key_B.pem" for the other node
neighbors_path = "/home/huutung/neighbors.txt"
authorized_list_path = "/home/huutung/authorized_list.txt"

peer_list = {}

class RsaApp(app_manager.RyuApp):
    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(RsaApp, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(RsaController, {'rsa_api_app': self})


# Load neighbor list from a file
def load_neighbors(file_path):
    with open(file_path, 'r') as file:
        neighbors = file.read().splitlines()
    return neighbors



# Load authorized list from a file
def load_authorized_list(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    # Regular expression to match each block
    pattern = re.compile(r'(controller-\d+)(.*?-----END RSA PUBLIC KEY-----)', re.DOTALL)

    matches = pattern.findall(content)

    keys_dict = {}
    for match in matches:
        label, key = match
        keys_dict[label] = key.strip()
        
    return keys_dict


# Load keys
def load_private_key(path):
    with open(path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

def load_public_key(path):
    with open(path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read(),backend=default_backend())
    return public_key

def load_public_key_pem(pem_data):
    return serialization.load_pem_public_key(
        pem_data.encode('utf-8'), 
        backend=default_backend()
    )


neighbor_list = load_neighbors(neighbors_path)
authorized_list = load_authorized_list(authorized_list_path)
private_key = load_private_key(private_key_path)
public_key = load_public_key(public_key_path)

#print("hostname: ", hostname, "\nneighbor list: ", neighbor_list, "\nprivate key: ", private_key, "\npublic key: ", public_key, "\nauthorized_list: ", authorized_list)
# Utility functions
def encrypt_with_public_key(public_key, message):
    return public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def decrypt_with_private_key(private_key, ciphertext):
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def sign_with_private_key(private_key, message):
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

def verify_signature(public_key, signature, message):
    print("enter verify")
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        print("verify finish")
        return True
    except ValueError:
        # Signature verification failed
        print("verify failed")
        return False
    except Exception as e:
        # Handle other exceptions
        print(f"Error during signature verification: {e}")
        return False
    
    

def compute_session_key(anonce, bnonce):
    return hashlib.sha256(anonce + bnonce).digest()

def encrypt_with_session_key(session_key, json_obj):
    # Convert JSON object to string
    plaintext = json.dumps(json_obj).encode()
    
    # Generate a random IV (Initialization Vector)
    iv = os.urandom(16)
    
    # Create a cipher object
    cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # Encrypt the plaintext
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    
    # Return the IV and ciphertext concatenated and encoded in base64
    return base64.b64encode(iv + ciphertext).decode()

def decrypt_with_session_key(session_key, encrypted_data):
    # Decode the base64 encoded data
    ciphertext = base64.b64decode(encrypted_data)
    
    # Extract the IV and the actual ciphertext
    iv = ciphertext[:16]
    ciphertext = ciphertext[16:]
    
    # Create a cipher object
    cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    # Decrypt the ciphertext
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Convert the plaintext back to a JSON object
    return json.loads(plaintext.decode())


class RsaController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(RsaController, self).__init__(req, link, data, **config)
        self.rsa_api_app = data['rsa_api_app']
        
    @route('rsa', '/rsa/test', methods=['GET'])
    def rsa_test(self, req, **kwargs):
        return Response(content_type='text/html', body=test_html)
    
    
    @route('rsa', '/p2p/join/{hostname_peer}', methods=['GET'])
    def send_message1(self, req, hostname_peer, **kwargs):
        print("===================", hostname, "Request to join " , hostname_peer, '\n')
        anonce = os.urandom(32)  # Replace with your Anonce generation logic
        print("========Anonce Created===========\n", anonce)
        if hostname_peer in authorized_list:
            public_key_peer = load_public_key_pem(authorized_list[hostname_peer])
            if hostname_peer not in peer_list:
                peer_list[hostname_peer] = [None, None, None]  # Initialize peer_list entry
            peer_list[hostname_peer][0] = anonce 
            # Encrypt Anonce with receiver's public key
            encrypted_anonce = encrypt_with_public_key(public_key_peer, anonce)
            print("========Anonce Encrypted===========\n", encrypted_anonce)
             # Prepare Message 1 JSON payload
            message1 = {
                "hostname": hostname,
                "anonce": base64.b64encode(encrypted_anonce).decode('utf-8')
            }
            # Send Message 1
            print('========Sending message 1===========\n', message1)
            end_point = '/message1'
            url = 'http://{0}:8080{1}'.format(hostname_peer,end_point)
            headers = {'Content-type': 'application/json'}
            data = json.dumps(message1)
            try:
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()  
                
            except requests.exceptions.RequestException as e:
                print(e)
            return
        else:
            return f"{hostname_peer} is not authorized."
    # Step 1: Receive and process Message 1 (Anonce)
    @route('rsa', '/message1', methods=['POST'])
    def receive_message1(self, req, **kwargs):
        json_str = req.body.decode('utf-8')
        data = json.loads(json.loads(json_str))
        print('========Received message 1===========\n', data)
        hostname_peer = data.get('hostname')
        encrypted_anonce = base64.b64decode(data.get('anonce'))

        if hostname_peer in authorized_list:
            public_key_peer = load_public_key_pem(authorized_list[hostname_peer])
            if hostname_peer not in peer_list:
                peer_list[hostname_peer] = [None, None, None]  # Initialize peer_list entry
            # Decrypt Anonce with own private key
            decrypted_anonce = decrypt_with_private_key(private_key, encrypted_anonce)

            print('========Decrypted Anonce===========\n', decrypted_anonce)
            #save anonce
            peer_list[hostname_peer][0] = decrypted_anonce
            # Generate Bnonce and sign Anonce
            bnonce = os.urandom(32)
            print("========Bnonce Created===========\n", bnonce)
            signed_anonce = sign_with_private_key(private_key, decrypted_anonce)
            print("========Anonce Signed===========\n", signed_anonce)

            #Save bnonce
            peer_list[hostname_peer][1] = bnonce
            # Encrypted Bnonce with peer public key
            encrypted_bnonce = encrypt_with_public_key(public_key_peer, bnonce)
            print("========Bnonce Encrypted===========\n", encrypted_bnonce)
            # Prepare Message 2 (hostname, signed_anonce, bnonce)
            message2 = {
                'hostname': hostname,
                'signed_anonce': base64.b64encode(signed_anonce).decode('utf-8'),
                'bnonce': base64.b64encode(encrypted_bnonce).decode('utf-8')
            }
            print('========Sending message 2===========\n', message2)
            # Send Message 2
            end_point = '/message2'
            url = 'http://{0}:8080{1}'.format(hostname_peer,end_point)
            headers = {'Content-type': 'application/json'}
            data = json.dumps(message2)
            try:
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()  
                
            except requests.exceptions.RequestException as e:
                print(e)
            return
        else:
            return json.dumps({'error': f"{hostname_peer} is not authorized."}), 403

    # Step 2: Receive and process Message 2 (Signed Anonce, Bnonce)
    @route('rsa', '/message2', methods=['POST'])
    def receive_message2(self, req, **kwargs):
        json_str = req.body.decode('utf-8')
        data = json.loads(json.loads(json_str))
        print('========Received message 2===========\n', data)
        hostname_peer = data.get('hostname')
        signed_anonce = base64.b64decode(data.get('signed_anonce'))
        bnonce_encoded = base64.b64decode(data.get('bnonce'))
      
        if hostname_peer in authorized_list:
            public_key_peer= load_public_key_pem(authorized_list[hostname_peer])
            print("peer_list: ", peer_list)
            anonce = peer_list[hostname_peer][0] 
            print("anonce", anonce)
            if verify_signature(public_key_peer, signed_anonce, anonce):

                print("========== Verify anonce_signed: MATCH ==========")
                # Decrypt Bnonce with own private key
                decrypted_bnonce = decrypt_with_private_key(private_key, bnonce_encoded)
                print('========Decrypted Bnonce===========\n', decrypted_bnonce)
                #Save bnonce
                peer_list[hostname_peer][1] = decrypted_bnonce
                print("peer_list: ", peer_list)
                # Prepare Message 3 (signed_bnonce)
                signed_bnonce = sign_with_private_key(private_key, decrypted_bnonce)
                print('========Signed Bnonce===========\n', signed_bnonce)
                message3 = {
                    'hostname': hostname,
                    'signed_bnonce': base64.b64encode(signed_bnonce).decode('utf-8')
                }
                end_point = '/message3'
                url = 'http://{0}:8080{1}'.format(hostname_peer, end_point)
                headers = {'Content-type': 'application/json'}
                data = json.dumps(message3)
                print('========Sending message 3===========\n', message3)
                try:
                    response = requests.post(url, json=data, headers=headers)
                    response.raise_for_status()  
                except requests.exceptions.RequestException as e:
                    print(e)
                return 
            else:
                return f"{hostname_peer} is not authorized."
        return

    # Step 3: Receive and process Message 3 (Signed Bnonce)
    @route('rsa', '/message3', methods=['POST'])
    def receive_message3(self, req, **kwargs):
        json_str = req.body.decode('utf-8')
        data = json.loads(json.loads(json_str))
        print('========Received message 3===========\n', data)
        hostname_peer = data.get('hostname')
        signed_bnonce = base64.b64decode(data.get('signed_bnonce'))


        if hostname_peer in authorized_list:
            public_key_peer = load_public_key_pem(authorized_list[hostname_peer])
            bnonce = peer_list[hostname_peer][1] 
        # Verify signed Bnonce
            if verify_signature(public_key_peer, signed_bnonce, bnonce):
                print("========== Verify bnonce_signed: MATCH ==========")
                # Prepare Message 4 (OK)
                message4 = {
                    'hostname': hostname,
                    'status': 'OK'
                }
                end_point = '/message4'
                url = 'http://{0}:8080{1}'.format(hostname_peer,end_point)
                headers = {'Content-type': 'application/json'}
                data = json.dumps(message4)
                print('========Sending message 4===========\n', message4)
                try:
                    response = requests.post(url, json=data, headers=headers)
                    response.raise_for_status()  
                except requests.exceptions.RequestException as e:
                    print(e)

                #save session key    
                anonce = peer_list[hostname_peer][0]
                bnonce = peer_list[hostname_peer][1]

                peer_list[hostname_peer][2] = compute_session_key(anonce, bnonce)
                print("final peer list: ", peer_list)
                save_peer_list('/home/huutung/peer_list.txt', peer_list)
                return 
            else:
                return {'error': "Signature verification failed for signed Bnonce."}
        return
    # Step 4: Receive and process Message 4 (OK)
    @route('rsa', '/message4', methods=['POST'])
    def receive_message4(self, req, **kwargs):
        json_str = req.body.decode('utf-8')
        data = json.loads(json.loads(json_str))
        print('========Received message 4===========\n', data)
        hostname_peer = data.get('hostname')
        status = data.get('status')
        
        if hostname_peer in authorized_list:
            if status == 'OK':
                # Add peer to peer list (or take other actions)
                # For example:
                anonce = peer_list[hostname_peer][0]
                bnonce = peer_list[hostname_peer][1]
                peer_list[hostname_peer][2] = compute_session_key(anonce, bnonce)
                print("peer list final", peer_list)
                save_peer_list('/home/huutung/peer_list.txt', peer_list)
            
                # drop local 
                local_db_name = 'sdn'
                remote_db_name = 'sdn'
                client = MongoClient('mongodb://localhost:27017/')
                remote_db_uri = f'mongodb://{hostname_peer}:27017'


                client.drop_database('sdn')
                print(f'Dropped local SDN database: {local_db_name}')

                # opy remote MongoDB database using mongodump and mongorestore
                # Create a dump of the remote MongoDB database
                dump_command = f'mongodump --uri="{remote_db_uri}" --db {remote_db_name} --out /tmp/mongodump'
                os.system(dump_command)
                print(f'Dumped remote database: {remote_db_name} to /tmp/mongodump')

                # Restore the dump to the local MongoDB instance
                restore_command = f'mongorestore --db {local_db_name} --dir /tmp/mongodump/{remote_db_name}'
                os.system(restore_command)
                print(f'Restored remote database: {remote_db_name} to local database: {local_db_name}')

                # Clean up the dump files
                os.system('rm -rf /tmp/mongodump')
                print('Cleaned up temporary dump files')        
                print('========MONGODB COPIED===========\n', data)
        return
    
    
    '''
    @route('rsa', '/send_secure/{hostname_peer}', methods=['POST'])
    def send_secure_message(self, req, hostname_peer, **kwargs):
        if hostname_peer in peer_list:
            session_key = peer_list[hostname_peer][2]
            message = ast.literal_eval(req.body.decode('utf-8'))
            print("message:", message)
            encrypted_message = encrypt_with_session_key(session_key, message)
            print("message", message, "encrypted message", encrypted_message)
            message_send = {
                'hostname': hostname,
                'encrypted_message': encrypted_message
            }
            end_point = '/secure_message'
            url = 'http://{0}:8080{1}'.format(hostname_peer, end_point)
            headers = {'Content-type': 'application/json'}
            data = json.dumps(message_send)
            try:
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()  
                print("Message sent to:", hostname_peer)
            except requests.exceptions.RequestException as e:
                print("Error sending message  to:", hostname_peer)
                print(e)
            return

    # Receive secure message endpoint
    @route('rsa', '/secure_message', methods=['POST'])
    def receive_secure_message(self, req, **kwargs):
        json_str = req.body.decode('utf-8')
        data = json.loads(json.loads(json_str))
        hostname_peer = data.get('hostname')
        message = data.get('encrypted_message')
        print("message", message)
        if hostname_peer in peer_list:
            session_key = peer_list[hostname_peer][2]
            decrypted_message = decrypt_with_session_key(session_key, message)
            print(f"Received message: {decrypted_message}")
            return "OK"
    '''

    # Endpoint to view neighbor list
    @route('rsa', '/neighbor_list', methods=['GET'])
    def get_neighbor_list():
        return json.dumps({'neighbors': neighbor_list}), 200


    # Endpoint to view peer list
    @route('rsa', '/peer_list', methods=['GET'])
    def get_peer_list():
        return json.dumps({'peers': peer_list}), 200

def save_peer_list(file_path, peer_list):
    with open(file_path, 'w') as file:
        # Iterate over the new_data dictionary
        for key, values in peer_list.items():
            file.write(f"{key}:\n")
            # Write each byte string in hexadecimal representation to the file
            for value in values:
                file.write(f"{value.hex()}\n")

def load_peer_list(file_path):
    peer_list_load = {}
    current_key = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.endswith(':'):
                current_key = line[:-1]
                peer_list_load[current_key] = []
            elif current_key is not None:
                peer_list_load[current_key].append(bytes.fromhex(line))

    return peer_list_load
