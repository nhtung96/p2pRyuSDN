

*At beginning:
i.Node A: 
i1.have an authorized list is public key list, authorized_list = [hostnameB:public_key_B]
i2.have public_key_A and private_key_A
i3.have neighbor list = [hostnameA]
i4.have peer list = [] 
i.Node B: 
i1.have an authorized list is public key list, authorized_list = [hostnameA:public_key_A]
i2.have public_key_B and private_key_B
i3.have neighbor list = [hostnameA]
i4.have peer list = [] 

*Node A init connection with node B:
1.node A send message 1 (hostnameA, Anonce) via HTTP POST to hostnameB. Anonce is the encrypted with public_key_B. 
2.node B check message 1 and check if hostnameA is in the authorized_list. If yes, node B decrypted Anonce with B's private key.
3.node B send message 2 (hostnameB, sign(Anonce), Bnonce) via HTTP POST to hostnameA. Bnonce is the encrypted nonce with public_key_A. sign(Anonce) is sign with B private key
4.node A receive message 2 and check if hostnameB is in the authorized_list and verify sign(Anonce). If both are OK, node A decrypted Bnonce with its private key and node A send message 3 (sign(Bnonce)) via HTTP POST to hostnameB. Sign(Bnonce) is sign with A private key.
5.If signBnonce is matched with Bnonce at node B, node B send message 4 to node A(OK) and add A to B's peer list.
6.If A received message 4 from B, node A will add node B in its peer list
7.Session key = sha256(Anonce + Bnonce) at 2 nodes
8.from now http body will be encrypted with sha256

*After 4 way handshake:
i.Node A: 
i1.have an authorized list is public key list, authorized_list = [public_key_B]
i2.have public_key_A and private_key_A
i3.have neighbor list = [hostnameB]
i4.have peer list = [hostnameB:sessionkey] 
i.Node B: 
i1.have an authorized list is public key list, authorized_list = [public_key_A]
i2.have public_key_B and private_key_B
i3.have neighbor list = [hostnameA]
i4.have peer list = [hostnameA:sessionkey] 



#private pem
ssh-keygen -p -f id_rsa -m PEM

#public key
ssh-keygen -f id_rsa.pub -e -m pem > id_rsa.pub.pem



#run ryu manager
ryu-manager --observe-links --app-lists /home/huutung/p2pRyuSDN/apps/tung_network_engine.py /home/huutung/p2pRyuSDN/apps/tung_network_common_handler.py /home/huutung/p2pRyuSDN/apps/tung_p2p_engine.py /home/huutung/ryu/ryu/app/gui_topology/gui_topology.py
show databases
use sdn
 db.dropDatabase()


Note:
Tạo 1 endpoint cho gửi/nhận. action nào data gì thì bỏ trong body http post json hết


curl -X GET http://controller-1:8080/p2p/join/controller-2


curl -X POST -d @large_json.json http://{hostname}:8080/stats/flowentry/add


curl -X POST -d '{
    "dpid": 1,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 0,
    "hard_timeout": 0,
    "priority": 1,
    "flags": 1,
    "match":{
        "in_port":1,
    },
    "instructions": [
        {
            "type": "APPLY_ACTIONS",
            "actions": [
                {
                    "max_len": 65535,
                    "port": 2,
                    "type": "OUTPUT"
                }
            ]
        }
    ]
 }' http://{hostname}:8080/stats/flowentry/add

curl -X POST -d '{
    "dpid": 2,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 0,
    "hard_timeout": 00,
    "priority": 1,
    "flags": 1,
    "match":{
        "in_port":1
    },
    "instructions": [
        {
            "type": "APPLY_ACTIONS",
            "actions": [
                {
                    "max_len": 65535,
                    "port": 2,
                    "type": "OUTPUT"
                }
            ]
        }
    ]
 }' http://localhost:8080/stats/flowentry/add


 curl -X POST -d '{
    "dpid": 1,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 0,
    "hard_timeout": 00,
    "priority": 1,
    "flags": 1,
    "match":{
        "in_port":2
    },
    "instructions": [
        {
            "type": "APPLY_ACTIONS",
            "actions": [
                {
                    "max_len": 65535,
                    "port": 1,
                    "type": "OUTPUT"
                }
            ]
        }
    ]
 }' http://localhost:8080/stats/flowentry/add

curl -X POST -d '{
    "dpid": 2,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 0,
    "hard_timeout": 00,
    "priority": 1,
    "flags": 1,
    "match":{
        "in_port":2
    },
    "instructions": [
        {
            "type": "APPLY_ACTIONS",
            "actions": [
                {
                    "max_len": 65535,
                    "port": 1,
                    "type": "OUTPUT"
                }
            ]
        }
    ]
 }' http://localhost:8080/stats/flowentry/add


