#!/usr/bin/env python3

import socket
import argparse
import select
from time import time
from sys import stderr
from operator import add
from functools import reduce


def hit_port_tcp(client_port, server_port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.bind((client_ip, client_port))
    # print ("Hitting port " + str(server_port), file=stderr)
    client_socket.connect((server_ip, server_port))
    client_socket.close()


def handle_ports(client_port, server_port):
    if server_port > (server_offset + max_index):
        # Handle special case server_port
        server_port -= server_offset + max_index
        if server_port == 1:
            bit_seq = "0" * bits
        elif server_port == 2:
            bit_seq = "1" * bits
        else:
            bit_seq = - (server_port - 3)  # -X in EOF-0, etc.
        index = client_port - client_offset - 1
    else:
        # Handle server port as index and client as bit-sequence
        bit_seq = bin(client_port - client_offset)[2:].zfill(bits)
        index = server_port - server_offset - 1
    return (index + 1, bit_seq)


ap = argparse.ArgumentParser()
ap.add_argument("-O","--server_offset",default=34000,type=int,help="Number of ports to step over before mapping offset+1, ..., to indexes. Default 34000 (in case running both server and client on same machine limit clashes)",)
ap.add_argument("-o","--client_offset",default=1024,type=int,help="Number of ports to step over before mapping offset+1, ..., to bit sequences. Default 1024 (running non-root)",)
ap.add_argument("-m","--max_index",default=248,type=int,help="Number of bit-sequences to send before waiting for acknowledgment from client",)
ap.add_argument("-b","--bits",default=8,type=int,help="Bit space assigned to each port. Default 8 bits",)
ap.add_argument("-t", "--timeout", default=2000,type=int,help="time to wait (ms) before writing off UDP missing packets and requesting again")
ap.add_argument("-i","--ip",default="0.0.0.0",type=str,help="IP address of this machine. Default 0.0.0.0",)
ap.add_argument("-w", "--windows_mode", action="store_true", help="Run in Windows-compatible mode")
ap.add_argument("-p","--poll_port",default=65535,type=int,help="Port to hit server on to receive next set of bits. Default 65535",)
ap.add_argument("-v", "--verbose", action="store_true", help="display helpful stats, (summary)")
ap.add_argument("-V", "--Verbose", action="store_true", help="display helpful stats, (explicit)")
args = vars(ap.parse_args())

client_ip = args["ip"]
timeout = args["timeout"]
windows_mode = args["windows_mode"]
poll_port = args["poll_port"]
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

if args["max_index"] > 2 ** bits - 8:
    print ("Max index value exceeded, using ", 2 ** bits - 8, file=stderr)
elif args["max_index"] % 8:
    print ("Max index must be divisible by 8, using ", int(args["max_index"] / 8) * 8, file=stderr)
elif args["max_index"] == 0:
    print ("Invalid Max index, using minimum value 8", file=stderr)
max_index = max(min(int(args["max_index"] / 8) * 8, 2 ** bits - 8), 8)

if args["server_offset"] > 65535 - 19 - max_index:
    print ("Server Offset value exceeded, using ", 65535 - 19 - max_index, file=stderr)
server_offset = min(args["server_offset"], 65535 - 19 - max_index)

server_ip = None
bit_buffer = [""] * max_index
eof_state, eof_index, eof_offset = False, -1, -1
last_buffer = ""
start_step = 0
connected = False
min_speed = 99999999999
max_speed = avg_speed = avg_count = 0

if windows_mode:
    port_array = []
else:
    poller = select.poll()
    fd_to_socket = {}
    READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR

# Set up server-poll TCP socket
wait_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
wait_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
wait_socket.bind((client_ip, poll_port))
wait_socket.listen(128)
# recv_socket, (recv_ip, recv_port) = wait_socket.accept() #Use later

# Setup UDP Data listeners
for port in range(client_offset + 1, client_offset + 2 ** bits - 1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # print ("listening on", port, file=stderr)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((client_ip, port))
    if not windows_mode:
        poller.register(sock, READ_ONLY)
        fd_to_socket[sock.fileno()] = sock
    else:
        port_array.append(sock)

while not eof_state:
    count = 0
    bit_buffer = [""] * max_index
    missing_indexes = set(range(max_index))
    bit_buffer = [last_buffer] + bit_buffer
    while count < max_index:
        readable = True
        while count < max_index and readable:
            # Recv data UDP
            if windows_mode:
                wait = timeout/1000 if last_buffer else None
                readable, _, _ = select.select(port_array, [], [], wait)
            else:
                wait = timeout if last_buffer else None
                readable = poller.poll(wait)
            if not connected:
                connected = True
                print ("Connection Established", file=stderr)
            for ready_server in readable:
                if not windows_mode:
                    fd, flag = ready_server
                    ready_server = fd_to_socket[fd]
                count += 1
                client_port = ready_server.getsockname()[1]
                recv_data, (server_ip, server_port) = ready_server.recvfrom(1)
                index, bit_seq = handle_ports(client_port, server_port)
                missing_indexes.remove(index-1)
                if isinstance(bit_seq, int):
                    # Handle EOF
                    eof_state, eof_index = True, index
                    eof_offset = [None, bit_seq][bool(bit_seq)]
                    missing_indexes -= set(range(index, max_index))
                    max_index = index
                else:
                    bit_buffer[index] = bit_seq
        # wait for all UDP data sent signal
        recv_socket, (server_ip, recv_port) = wait_socket.accept()
        recv_socket.close()
        # Send missing count (zero-indexed)
        missing_count = len(missing_indexes)
        hit_port_tcp(0, server_offset + missing_count + 1)
        # wait for ACK of no missing
        recv_socket, (server_ip, recv_port) = wait_socket.accept()
        recv_socket.close()
        # Send missing indexes (zero-indexed)
        for missing_index in missing_indexes:
            hit_port_tcp(0, server_offset + missing_index + 1)
    # All data received
    bit_buffer = bit_buffer[:count+1]
    if eof_state:
        bit_buffer[eof_index - 1] = bit_buffer[eof_index - 1][:eof_offset]
        for sock in fd_to_socket.values() if not windows_mode else port_array:
            sock.close()
    last_buffer = bit_buffer.pop()
    print (reduce(add, bit_buffer))

    if verbose:
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

print(last_buffer)
print ("Done!", file=stderr)
if verbose:
    print ("Max speed %.5fkB/s; Avg speed %.5fkB/s; Min speed %.5fkB/s"% (max_speed, avg_speed, min_speed), file=stderr)
