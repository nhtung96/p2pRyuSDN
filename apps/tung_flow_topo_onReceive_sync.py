# Copyright (C) 2013 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import socket

from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import Response
from ryu.app.wsgi import route
from ryu.app.wsgi import WSGIApplication
from ryu.base import app_manager
from ryu.lib import dpid as dpid_lib
from ryu.topology.api import get_switch, get_link, get_host

from rsa_api import load_peer_list
from rsa_api import decrypt_with_session_key
from rsa_api import encrypt_with_session_key

#tung
from pymongo import MongoClient
import requests
import ast
import time
# REST API for switch configuration
#
# get all the switches
# GET /v1.0/topology/switches
#
# get the switch
# GET /v1.0/topology/switches/<dpid>
#
# get all the links
# GET /v1.0/topology/links
#
# get the links of a switch
# GET /v1.0/topology/links/<dpid>
#
# get all the hosts
# GET /v1.0/topology/hosts
#
# get the hosts of a switch
# GET /v1.0/topology/hosts/<dpid>
#
# where
# <dpid>: datapath id in 16 hex

hostname = socket.gethostname() 

#tung
def send_secure_topology(topo, peers_to_exclude, peers):
    end_point = '/secure-data'
    peers_to_update = [p for p in peers if p not in peers_to_exclude]
    peers_to_exclude = peers_to_exclude + peers_to_update 
    for peer in peers_to_update:
        time.sleep(10)
        url = 'http://{0}:8080{1}'.format(peer,end_point)
        headers = {'Content-type': 'application/json'}
        data = {'action': 'topology-update', 'exclude': peers_to_exclude, 'topology': topo}
        session_key = peers[peer][2]
        encrypted_data = encrypt_with_session_key(session_key, data)
        message_send = {
                'hostname': hostname,
                'encrypted_message': encrypted_data
            }
        try:
            response = requests.post(url, json=message_send, headers=headers)
            response.raise_for_status()  
            print("Sent secure topology successfully to:", peer)
        except requests.exceptions.RequestException as e:
            print("Error to send to:", peer)
            print(e)

#tung
def send_secure_flow(flow, peers_to_exclude, peers, action):
    end_point = '/secure-data'
    peers_to_update = [p for p in peers if p not in peers_to_exclude]
    peers_to_exclude = peers_to_exclude + peers_to_update
    for peer in peers_to_update:
        time.sleep(10)
        url = 'http://{0}:8080{1}'.format(peer,end_point)
        headers = {'Content-type': 'application/json'}
        session_key = peers[peer][2]
        data = {'action': action, 'exclude': peers_to_exclude, 'flow': flow}
        encrypted_data = encrypt_with_session_key(session_key, data)
        message_send = {
                'hostname': hostname,
                'encrypted_message': encrypted_data
            }
        try:
            response = requests.post(url, json=message_send, headers=headers)
            response.raise_for_status()  
            print("Sent secure flow successfully to:", peer)
        except requests.exceptions.RequestException as e:
            print("Error to send to:", peer)
            print(e)  

class TopologyAPI(app_manager.RyuApp):
    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(TopologyAPI, self).__init__(*args, **kwargs)

        wsgi = kwargs['wsgi']
        wsgi.register(TopologyController, {'topology_api_app': self})


class TopologyController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(TopologyController, self).__init__(req, link, data, **config)
        self.topology_api_app = data['topology_api_app']

    @route('topology', '/v1.0/topology/switches',
           methods=['GET'])
    def list_switches(self, req, **kwargs):
        return self._switches(req, **kwargs)

    @route('topology', '/v1.0/topology/switches/{dpid}',
           methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def get_switch(self, req, **kwargs):           
        return self._switches(req, **kwargs)

    @route('topology', '/v1.0/topology/links',
           methods=['GET'])
    def list_links(self, req, **kwargs):
        return self._links(req, **kwargs)

    @route('topology', '/v1.0/topology/links/{dpid}',
           methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def get_links(self, req, **kwargs):
        return self._links(req, **kwargs)

    @route('topology', '/v1.0/topology/hosts',
           methods=['GET'])
    def list_hosts(self, req, **kwargs):
        return self._hosts(req, **kwargs)

    @route('topology', '/v1.0/topology/hosts/{dpid}',
           methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def get_hosts(self, req, **kwargs):
        return self._hosts(req, **kwargs)
    

    @route('flow', '/secure-data',
           methods=['POST'])
    def onReceive_secure_data(self, req, **kwargs):
        # Get message
        json_str = req.body.decode('utf-8')
        data = json.loads(json.loads(json_str))
        
        # Decrypt message
        peers = load_peer_list('/home/huutung/peer_list.txt')
        hostname_peer = data.get('hostname')       
        session_key = peers[hostname_peer][2]
        decrypted_message = decrypt_with_session_key(session_key, data)
        
        peers_to_exclude = data['exclude']
        action = decrypted_message['action']

        if action == 'insert':
            flow = decrypted_message['flow']
            client = MongoClient('mongodb://localhost:27017/')
            db = client['sdn']  
            collection = db['flows']  
            collection.insert_one(flow)
            client.close()
            send_secure_flow(flow, peers_to_exclude, peers, action)

        elif action == 'delete':
            flow = decrypted_message['flow']
            client = MongoClient('mongodb://localhost:27017/')
            db = client['sdn']  
            collection = db['flows']  
            collection.delete_one(flow)
            client.close()
            send_secure_flow(flow, peers_to_exclude, peers, action)

        elif action == 'topology-update':
            topo = decrypted_message['topology']
            client = MongoClient('mongodb://localhost:27017/')
            db = client['sdn']  
            collection = db['topology']  
            query = {'domain': hostname_peer, 'record': 1}
            update_data = {'$set': {'topo': topo}}
            collection.update_one(query, update_data)
            client.close()
            send_secure_topology(topo, peers_to_exclude, peers)
        else: 
            print("Invalid action")

        return 
    
    #tung
    @route('topology', '/p2p/topology/global',
           methods=['GET'])
    def get_global_topology(self, req, **kwargs):
        client = MongoClient('mongodb://localhost:27017/')
        db = client['sdn']
        collection = db['topology']
        topology = collection.find({}, {"record":1})
        body = json.dumps([item for item in topology])
        client.close()
        return Response(content_type='application/json', body=body)
    #tung
    @route('topology', '/p2p/topology',
           methods=['GET'])
    def get_local_topology(self, req, **kwargs):
        return self._topology(req, **kwargs)
    #tung
    @route('flows', '/p2p/flows',
           methods=['GET'])
    def get_full_flows(self, req, **kwargs):
        client = MongoClient('mongodb://localhost:27017/')
        db = client['sdn']
        collection = db['flows']
        flows = collection.find({}, {"_id":0})
        body = json.dumps([flow for flow in flows])
        client.close()
        return Response(content_type='application/json', body=body)

    def _switches(self, req, **kwargs):
        dpid = None
        if 'dpid' in kwargs:
            dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        switches = get_switch(self.topology_api_app, dpid)
        body = json.dumps([switch.to_dict() for switch in switches])
        return Response(content_type='application/json', body=body)

    def _links(self, req, **kwargs):
        dpid = None
        if 'dpid' in kwargs:
            dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        links = get_link(self.topology_api_app, dpid)
        body = json.dumps([link.to_dict() for link in links])
        return Response(content_type='application/json', body=body)

    def _hosts(self, req, **kwargs):
        dpid = None
        if 'dpid' in kwargs:
            dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        hosts = get_host(self.topology_api_app, dpid)
        body = json.dumps([host.to_dict() for host in hosts])
        return Response(content_type='application/json', body=body)
    
    #tung
    def _topology(self, req, **kwargs):
        dpid = None
        if 'dpid' in kwargs:
            dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        # Get switches
        switch_list = get_switch(self.topology_api_app, dpid)
        switches = [switch.to_dict() for switch in switch_list]
        # Get links
        links_list = get_link(self.topology_api_app, dpid)
        links = [link.to_dict() for link in links_list]

        # Get hosts (which are learned at switch ports)
        host_list = get_host(self.topology_api_app, dpid)
        ports = []
        for switch in switch_list:
            ports += switch.ports
        port_macs = [p.hw_addr for p in ports]
        n_host_list = [h for h in host_list if h.port.hw_addr in port_macs]
        hosts = [h.to_dict() for h in n_host_list]

        topology = {"switches": switches, "links": links, "hosts": hosts}

        client = MongoClient('mongodb://localhost:27017/')
        db = client['sdn']
        collection = db['topology']
        collection.delete_one({'domain': hostname})
        collection.insert_one({'domain': hostname, 'record': 1, 'topo': topology})
        client.close()
        body = json.dumps(topology)

        #load peers to send p2p topology update
        peers = load_peer_list('/home/huutung/peer_list.txt')

        #exclude local 
        excluded_list = [hostname]

        #send update to all peers
        send_secure_topology(body, excluded_list, peers)
        
        return Response(content_type='application/json', body=body)

