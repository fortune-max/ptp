#!/usr/bin/env python2

import socket
import argparse
import select
from sys import stderr
from operator import add


def hit_port(client_port, server_port):
    client_socket = socket.socket()
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if client_port:
        client_socket.bind((client_ip, client_port))
    # print >> stderr, "Hitting port " + str(server_port)
    client_socket.connect((server_ip, server_port))
    client_socket.close()


def handle_ports(client_port, server_port):
    if server_port > (server_offset + max_index):
        # Handle special case server_port
        server_port -= server_offset + max_index
        if server_port == 1:
            bit_seq = "0" * bits
            index = client_port - client_offset - 1
        elif server_port == 2:
            bit_seq = "1" * bits
            index = client_port - client_offset - 1
        else:
            bit_seq = "-%d" % (server_port - 3)  # -X in EOF-0, etc.
            index = client_port - client_offset - 1
    else:
        # Handle server port as index and client as bit-sequence
        bit_seq = bin(client_port - client_offset)[2:].zfill(bits)
        index = server_port - server_offset - 1
    return (index, bit_seq)


ap = argparse.ArgumentParser()

ap.add_argument("-O","--server_offset",default=34000,type=int,help="Number of ports to step over before mapping offset+1, ..., to indexes. Default 34000 (in case running both server and client on same machine limit clashes)",)
ap.add_argument("-o","--client_offset",default=1024,type=int,help="Number of ports to step over before mapping offset+1, ..., to bit sequences. Default 1024 (running non-root)",)
ap.add_argument("-m","--max_index",default=24,type=int,help="Number of bit-sequences to send before waiting for acknowledgment from client",)
ap.add_argument("-b","--bits",default=5,type=int,help="Bit space assigned to each port. Default 8 bits",)
ap.add_argument("-i","--ip",default="0.0.0.0",type=str,help="IP address of this machine. Default 0.0.0.0",)
args = vars(ap.parse_args())

client_ip = args["ip"]
if args["bits"] < 4:
    print >> stderr, "Minimum bits is 4, using ", 4
elif args["bits"] > 16:
    print >> stderr, "Maximum bits exceeded, using ", 16
bits = max(min(args["bits"], 16), 4)

if args["client_offset"] > 65534 - 2 ** bits + 2:
    print >> stderr, "Client Offset value exceeded, using ", 65534 - 2 ** bits + 2
client_offset = min(args["client_offset"], 65534 - 2 ** bits + 2)

if args["max_index"] > 2 ** bits - 8:
    print >> stderr, "Max index value exceeded, using ", 2 ** bits - 8
elif args["max_index"] % 8:
    print >> stderr, "Max index must be divisible by 8, using ", args["max_index"] / 8 * 8
elif args["max_index"] == 0:
    print >> stderr, "Invalid Max index, using minimum value 8"
max_index = max(min(args["max_index"] / 8 * 8, 2 ** bits - 8), 8)

if args["server_offset"] > 65535 - 19 - max_index:
    print >> stderr, "Server Offset value exceeded, using ", 65535 - 19 - max_index
server_offset = min(args["server_offset"], 65535 - 19 - max_index)


server_ip = None
port_array = []
bit_buffer = [""] * max_index
eof_state, eof_index, eof_offset = False, -1, -1

for port in range(client_offset + 1, client_offset + 2 ** bits - 1):
    sock = socket.socket()
    # print >>stderr, "listening on", port
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((client_ip, port))
    sock.listen(1)
    port_array.append(sock)

while not eof_state:
    count = 0
    while count < max_index:
        readable, _, _ = select.select(port_array, [], [])
        for ready_server in readable:
            count += 1
            client_port = ready_server.getsockname()[1]
            recv_socket, (server_ip, server_port) = ready_server.accept()
            recv_socket.close()
            index, bit_seq = handle_ports(client_port, server_port)
            if bit_seq.startswith("-"):
                # Handle EOF
                eof_state, eof_index = True, index
                eof_offset = None if bit_seq == "-0" else int(bit_seq)
                max_index = index + 1
            else:
                bit_buffer[index] = bit_seq
        if eof_state:
            bit_buffer[eof_index - 1] = bit_buffer[eof_index - 1][:eof_offset]
    print reduce(add, bit_buffer)
    if not eof_state:
        bit_buffer = [""] * max_index
        hit_port(0, 65535)
