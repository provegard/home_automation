import socket
import struct
from datetime import datetime, timedelta
import http.server
import json
import threading

# Multicast group details
MCAST_GRP = "234.222.250.1"
MCAST_PORT = 57082

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Allow multiple sockets to use the same PORT number
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind to the port that we know will receive multicast data
sock.bind(('', MCAST_PORT))

# Tell the kernel that we are a multicast socket
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY))

Epoch = datetime(1970, 1, 1)

class SharedData:
    def __init__(self, data):
        self.data = data
        self.lock = threading.Lock()

    def update_data(self, new_data):
        with self.lock:
            self.data = new_data

    def get_data(self):
        with self.lock:
            return self.data

empty_readings = {
    "timestamp_utc": "",
    "serial": "",
    "phase1_amps": 0,
    "phase2_amps": 0,
    "phase3_amps": 0
}

# Shared readings, updated by the reader loop and served as JSON by the HTTP server.
shared_readings = SharedData(empty_readings)

class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        data = shared_readings.get_data()
        self.wfile.write(json.dumps(data).encode())

def run_server():
    server_address = ("0.0.0.0", 8000)
    httpd = http.server.HTTPServer(server_address, SimpleHTTPRequestHandler)
    print("Serving on port 8000...")
    httpd.serve_forever()


def print_unknown(data, size, offs = 0):
    print("size = %d, offset = %d" % (size, offs))
    i = offs
    while i < len(data):
        chunk = data[i:i+size]
        num = int.from_bytes(chunk, "little")
        print("- offset %d: %d (%s)" % (i, num, hex(num)))
        i += size

def read_data():
    # Receive the data, note that this is a blocking call
    while True:
        data, _ = sock.recvfrom(10240)

        # L437704C1A4
        first = data[0:2].decode("ascii")
        serial = data[2:11].decode("ascii")
        millis = int.from_bytes(data[11:19], "little")
        timestamp = Epoch + timedelta(milliseconds = millis)
        unknown = data[19:30]
        version = data[30:38].decode("ascii")

        phase_1 = int.from_bytes(unknown[1:3], "little") / 1000.0
        phase_2 = int.from_bytes(unknown[4:6], "little") / 1000.0
        phase_3 = int.from_bytes(unknown[7:9], "little") / 1000.0

        latest_readings = {
            "timestamp_utc": str(timestamp),
            "serial": serial,
            "phase1_amps": phase_1,
            "phase2_amps": phase_2,
            "phase3_amps": phase_3
        }
        shared_readings.update_data(latest_readings)

        #print("---")
        #print("first two: %s" % (first, ))
        #print("serial   : %s" % (serial, ))
        #print("time UTC : %s" % (timestamp, ))
        #print("version  : %s" % (version, ))
        #print("phase 1  : %.2f" % (phase_1, ))
        #print("phase 2  : %.2f" % (phase_2, ))
        #print("phase 3  : %.2f" % (phase_3, ))
        #print("-")
        #print_unknown(unknown, 1)
        #print_unknown(unknown, 2)
        #print_unknown(unknown, 4)
        #print_unknown(unknown, 1, 1)
        #print_unknown(unknown, 2, 1)
        #print_unknown(unknown, 4, 1)

if __name__ == "__main__":
    # Create a thread to run the server
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    read_data()

