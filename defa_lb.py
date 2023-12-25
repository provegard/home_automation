import socket
import struct
from datetime import datetime, timedelta

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

def print_unknown(data, size, offs = 0):
    print("size = %d, offset = %d" % (size, offs))
    i = offs
    while i < len(data):
        chunk = data[i:i+size]
        num = int.from_bytes(chunk, "little")
        print("- offset %d: %d" % (i, num))
        i += size

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

    print("---")
    print("first two: %s" % (first, ))
    print("serial   : %s" % (serial, ))
    print("time UTC : %s" % (timestamp, ))
    print("version  : %s" % (version, ))
    print("phase 1  : %.2f" % (phase_1, ))
    print("phase 2  : %.2f" % (phase_2, ))
    print("phase 3  : %.2f" % (phase_3, ))
    print("-")
    #print_unknown(unknown, 1)
    #print_unknown(unknown, 2)
    #print_unknown(unknown, 4)
    #print_unknown(unknown, 1, 1)
    #print_unknown(unknown, 2, 1)
    #print_unknown(unknown, 4, 1)
    
