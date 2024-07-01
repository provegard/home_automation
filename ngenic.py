import http.client
import json
import os

HOST = "app.ngenic.se"
API_BASE = "/api/v3"

def read_pat():
    config_path = os.path.expanduser("~/.ngenic")
    with open(config_path, "r") as file:
        return file.readline().strip()

# Read the Personal Access token
PAT = read_pat()

connection = http.client.HTTPSConnection(HOST)
headers = {
    "Authorization": f"Bearer {PAT}"
}

def call_api(endpoint):
    connection.request("GET", f"{API_BASE}{endpoint}", headers=headers)
    response = connection.getresponse()
    ct = response.getheader("Content-Type")
    body = response.read().decode()
    if ct is not None and ct.startswith("application/json"):
        return json.loads(body)
    return body


# Get tunes - we expect a single one
tunes = call_api("/tunes")
if len(tunes) != 1:
    raise Exception(f"Unexpected tunes count: {len(tunes)}")
tune = tunes[0]
tuneId = tune["tuneUuid"]

nodes = call_api(f"/tunes/{tuneId}/gateway/nodes")
print(nodes)

rooms = call_api(f"/tunes/{tuneId}/rooms")
for room in rooms:
    name = room["name"]
    print(f"Room {name}")
    nodeId = room["nodeUuid"]
    types = call_api(f"/tunes/{tuneId}/measurements/{nodeId}/types")
    for type in types:
        value = call_api(f"/tunes/{tuneId}/measurements/{nodeId}/latest?type={type}")
        print(f"- type {type}: {value}")


connection.close()
