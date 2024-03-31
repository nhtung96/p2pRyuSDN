import requests
from pymongo import MongoClient

# Replace with your Ryu controller's URL
RYU_CONTROLLER_URL = 'http://localhost:8081'
DPID = '1'  # Replace with your switch Datapath ID

# MongoDB connection details
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DATABASE = 'sdn_data'
MONGODB_COLLECTION = 'flow_entries'

def get_flow_entries():
    url = f'{RYU_CONTROLLER_URL}/stats/flow/{DPID}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()  # Extract JSON content from the response
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving flow entries: {e}")
        return None

def store_in_mongodb(flow_entries):
    client = MongoClient(MONGODB_HOST, MONGODB_PORT)
    db = client[MONGODB_DATABASE]
    collection = db[MONGODB_COLLECTION]

    # Clear existing entries for the switch DPID
    collection.delete_many({'key': DPID})

    # Store new entries
    collection.insert_one({'key': DPID, 'flows': flow_entries})
    client.close()

if __name__ == '__main__':
    flow_entries = get_flow_entries()

    if flow_entries is not None:
        store_in_mongodb(flow_entries)
        print(f"Flow entries synchronized and stored in MongoDB for switch DPID {DPID}.")
    else:
        print(f"No flow entries found for switch DPID {DPID}.")
