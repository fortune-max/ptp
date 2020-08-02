#!/usr/bin/env python3

import socket
import select
import argparse
from sys import stdin, stderr
from math import ceil
from time import time
from operator import add
from functools import reduce


def hit_port_udp(server_port, client_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_ip, server_port))
    # print ("Hitting port ", server_port, client_port, file=stderr)
    server_socket.sendto(b"p", (client, client_port))
    server_socket.close()


def hit_port_tcp(server_port, client_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_ip, server_port))
    # print ("Hitting port ", server_port, client_port, file=stderr)
    server_socket.connect((client, client_port))
    server_socket.close()


def resolve_ports(bit_seq, server_is_idx, idx):
    server_port = server_offset + 1 + [0, idx][server_is_idx]
    client_port = client_offset + 1 + [idx, 0][server_is_idx]

    if len(set(bit_seq)) == 1:
        if server_is_idx:
            return resolve_ports(bit_seq, False, idx)
        server_port += max_index + int(bit_seq[0])
    else:
        if bit_seq[0] == "+":
            if server_is_idx:
                return resolve_ports(bit_seq, False, idx)
            server_port += max_index + eval(bit_seq) + 2
        else:
            client_port += int(bit_seq, 2) - 1
    hit_port_udp(server_port, client_port)


ap = argparse.ArgumentParser()
ap.add_argument("-O","--server_offset",default=34000,type=int,help="Number of ports to step over before mapping offset+1, ..., to indexes. Default 34000 (in case running both server and client on same machine limit clashes)",)
ap.add_argument("-o","--client_offset",default=1024,type=int,help="Number of ports to step over before mapping offset+1, ..., to bit sequences. Default 1024 (running non-root)",)
ap.add_argument("-m","--max_index",type=int,help="Number of bit-sequences to send before waiting for acknowledgment from client",)
ap.add_argument("-b","--bits",default=8,type=int,help="Bit space assigned to each port. Default 8 bits",)
ap.add_argument("-f", "--file", default="-", type=str, help="Input file to serve. Default stdin")
ap.add_argument("-w", "--windows_mode", action="store_true", help="Run in Windows-compatible mode")
ap.add_argument("-i","--ip",default="0.0.0.0",type=str,help="IP address of this machine. Default 0.0.0.0",)
ap.add_argument("-c","--client",default="127.0.0.1",type=str,help="Client IP to serve file to. Default localhost",)
ap.add_argument("-p","--poll_port",default=65535,type=int,help="Port to hit server on to receive next set of bits. Default 65535",)
ap.add_argument("-v", "--verbose", action="store_true", help="display helpful stats, (summary)")
ap.add_argument("-V", "--Verbose", action="store_true", help="display helpful stats, (explicit)")
args = vars(ap.parse_args())

client = args["client"]
input_stream = args["file"]
server_ip = args["ip"]
poll_port = args["poll_port"]
windows_mode = args["windows_mode"]
Verbose = args["Verbose"]
verbose = args["verbose"] or Verbose

if args["bits"] < 4:
    print ("Minimum bits is 4, using ", 4, file=stderr)
elif args["bits"] > 16:
    print ("Maximum bits exceeded, using ", 16, file=stderr)
bits = max(min(args["bits"], 16), 4)

if args["client_offset"] > 65534 - 2 ** bits + 2:
    print ("Client Offset value exceeded, using ", 65534 - 2 ** bits + 2, file=stderr)
client_offset = min(args["client_offset"], 65534 - 2 ** bits + 2)

max_index = args["max_index"] or (2 ** bits - 8)
if max_index > 2 ** bits - 8:
    print ("Max index value exceeded, using ", 2 ** bits - 8, file=stderr)
elif max_index % 8:
    print ("Max index must be divisible by 8, using ", int(args["max_index"] / 8) * 8, file=stderr)
elif max_index == 0:
    print ("Invalid Max index, using minimum value 8", file=stderr)
max_index = max(min(int(max_index / 8) * 8, 2 ** bits - 8), 8)

if args["server_offset"] > 65535 - 19 - max_index:
    print ("Server Offset value exceeded, using ", 65535 - 19 - max_index, file=stderr)
server_offset = min(args["server_offset"], 65535 - 19 - max_index)

if input_stream == "-":
    bytes = stdin.buffer
else:
    bytes = open(input_stream, "rb")

if windows_mode:
    port_array = []
else:
    poller = select.poll()
    fd_to_socket = {}
    READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR

# Set up TCP index listeners
for port in range(server_offset + 1, server_offset + max_index + 1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # print ("listening on", port, file=stderr)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((server_ip, port))
    # max value in /proc/sys/net/core/somaxconn, increase if higher than 128
    sock.listen(128)
    if not windows_mode:
        poller.register(sock, READ_ONLY)
        fd_to_socket[sock.fileno()] = sock
    else:
        port_array.append(sock)

connected = False
EOF = False
missing_count = 0
chunksize = int(max_index / 8) * bits
start_step = 0
min_speed = 99999999999
max_speed = avg_speed = avg_count = 0

while True:
    if not missing_count:
        if not EOF:
            step_duration = (time() - start_step)
            kbytes = max_index * bits / 8000
            speed = kbytes/step_duration
            if start_step:
                max_speed = max(speed, max_speed)
                min_speed = min(speed, min_speed)
                avg_speed = (avg_speed * avg_count + speed) / (avg_count + 1)
                avg_count += 1
                if Verbose:
                    print ("%.2fkB/s"%speed, file=stderr)
            start_step = time()

        chunks = bytes.read(chunksize)
        if not chunks and EOF:
            break
        bit_seq = reduce(add, map(lambda x: bin(x)[2:].zfill(8), chunks), "")
        segments = min(max_index, int(ceil(len(bit_seq) / bits)))
        if segments != max_index:
            EOF = True
            EOF_offset = (bits - len(bit_seq)) % bits
            bit_seq += "0" * EOF_offset
            bit_seq += str(EOF_offset).rjust(bits,"+")
            segments += 1
    for idx in set(missing_indexes) & set(range(segments)) if missing_count else range(segments):
        to_send = bit_seq[idx * bits : (idx + 1) * bits]
        # Send Data UDP
        resolve_ports(to_send, True, idx)
    #print ("Sent data UDP")
    # Notify client that data sent
    hit_port_tcp(0, poll_port)
    if not connected:
        connected = True
        print ("Connection Established")
    #print ("Notified send finish")
    # Get count of missing indexes
    if windows_mode:
        readable, _, _ = select.select(port_array, [], [])
    else:
        readable = poller.poll()
    ready_server = readable[0]
    if not windows_mode:
        ready_server = fd_to_socket[ready_server[0]]
    server_port = ready_server.getsockname()[1]
    recv_socket, (recv_ip, recv_port) = ready_server.accept()
    recv_socket.close()
    missing_count = server_port - server_offset - 1
    if missing_count and verbose:
        print ("Received count missing=", missing_count)
    # Notify client that count received
    hit_port_tcp(0, poll_port)
    #print ("Notified count received")
    # Receive ${missing_count} indexes missing
    count, missing_indexes = 0, []
    while count < missing_count:
        if windows_mode:
            readable, _, _ = select.select(port_array, [], [])
        else:
            readable = poller.poll()
        for ready_server in readable:
            if not windows_mode:
                ready_server = fd_to_socket[ready_server[0]]
            count += 1
            server_port = ready_server.getsockname()[1]
            recv_socket, (recv_ip, recv_port) = ready_server.accept()
            recv_socket.close()
            missing_indexes.append(server_port - server_offset - 1)
    #print ("Received indexes", missing_indexes)
print ("Max speed %.5fkB/s; Avg speed %.5fkB/s; Min speed %.5fkB/s"% (max_speed, avg_speed, min_speed))
print ("Done!")
