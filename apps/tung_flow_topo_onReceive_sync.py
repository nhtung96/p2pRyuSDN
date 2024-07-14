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

from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import Response
from ryu.app.wsgi import route
from ryu.app.wsgi import WSGIApplication
from ryu.base import app_manager
from ryu.lib import dpid as dpid_lib
from ryu.topology.api import get_switch, get_link, get_host

#tung
from pymongo import MongoClient
import requests
import ast
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

#tung
def topology_update(data, peers_to_exclude):
	end_point = '/sync/topology/update'
	peers_to_update = [p for p in peers if p in peers_to_exclude]
	for peer in peers_to_update:
		url = 'http://{0}{1}'.format(peer,end_point)
		requests.post(url,json=data)
		print(url)

#tung
def insert_flow(flow, peers_to_exclude=None, peers=None):
    end_point = '/sync/flow/insert'
    peers_to_update = [p for p in peers if p not in peers_to_exclude]
    print(peers_to_update)
    peers_to_exclude = peers_to_exclude + peers_to_update
    for peer in peers_to_update:
        time.sleep(10)
        url = 'http://{0}{1}'.format(peer,end_point)
        headers = {'Content-type': 'application/json'}
        print(url)
        data = {'exclude': excluded_lists, 'flow': flow}
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()  
            print("Flow inserted successfully at:", url)
        except requests.exceptions.RequestException as e:
            print("Error inserting flow at:", url)
            print(e)

#tung
def delete_flow(flow, peers_to_exclude):
    end_point = '/sync/flow/delete'
    peers_to_update = [p for p in peers if p in peers_to_exclude]
    for peer in peers_to_update:
        url = 'http://{0}{1}'.format(peer,end_point)
        headers = {'Content-type': 'application/json'}
        requests.post(url,json=flow,headers=headers)
        print(url)

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
    
    #tung
    @route('topology', '/tung/topology',
           methods=['GET'])
    def get_local_topology(self, req, **kwargs):
        return self._topology(req, **kwargs)
    
    #custom p2p msg coming
    @route('flow', '/sync/flow/insert',
           methods=['POST'])
    def onReceive_insert(self, req, **kwargs):
        data = ast.literal_eval(req.body.decode('utf-8'))
        flow = data['flow']
        peers_to_exclude = data['exlude']
        print(peers_to_exclude)
        client = MongoClient('mongodb://localhost:27017/')
        db = client['sdn']  
        collection = db['flows']  
        collection.insert_one(flow)
        client.close()
        return 
    #custom p2p msg coming
    @route('flow', '/sync/flow/delete',
           methods=['POST'])
    def onReceive_delete(self, req, **kwargs):
        data = ast.literal_eval(req.body.decode('utf-8'))
        flow = data['flow']
        peers_to_exclude = data['exlude']
        print(peers_to_exclude)
        client = MongoClient('mongodb://localhost:27017/')
        db = client['sdn']  
        collection = db['flows']  
        collection.delete_one(flow)
        client.close()
        return 
        #tung
    @route('topology', '/tung/topology/global',
           methods=['GET'])
    def get_global_topology(self, req, **kwargs):
        client = MongoClient('mongodb://localhost:27017/')
        db = client['sdn']
        collection = db['topology']
        topology = collection.find({}, {"_id":0})
        body = json.dumps([item for item in topology])
        client.close()
        return Response(content_type='application/json', body=body)
    
    #tung
    @route('flows', '/tung/flows',
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
        collection.delete_one({'domain': 1})
        collection.insert_one({'domain': 1, 'data':topology})
        client.close()

        body = json.dumps(topology)
        return Response(content_type='application/json', body=body)

