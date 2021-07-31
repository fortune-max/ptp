#!/usr/bin/env python3

import socket
import select
import argparse
from time import time
from sys import stderr
from multiprocessing import Process, Pipe


def hit_port(client_port, server_port):
    client_socket = socket.socket()
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if client_port:
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
ap.add_argument("-m","--max_index",default=248,type=int,help="Number of bit-sequences to send before waiting for acknowledgment from client",)
ap.add_argument("-b","--bits",default=8,type=int,help="Bit space assigned to each port. Default 8 bits",)
ap.add_argument("-i","--ip",default="0.0.0.0",type=str,help="IP address of this machine. Default 0.0.0.0",)
ap.add_argument("-s","--server",type=str,help="IP address of server machine",)
ap.add_argument("-p","--poll_port",default=65535,type=int,help="Port to hit server on to receive next set of bits. Default 65535",)
ap.add_argument("-v", "--verbose", action="store_true", help="display helpful stats, (slows performance)")
ap.add_argument("-P","--procs",default=1,type=int,help="How many extra processes to spawn to speed up transfer. Default 1",)
args = vars(ap.parse_args())

client_ip = args["ip"]
poll_port = args["poll_port"]
verbose = args["verbose"]
server_ip = args["server"]
procs = args["procs"]

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

bit_buffer = [""] * max_index
eof_state, eof_index, eof_offset = False, -1, -1
start_step = 0


def set_up_ports(idx, procs=procs):
    poller = select.poll()
    fd_to_socket = {}
    READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR

    for port in range(client_offset + idx, client_offset + 2 ** bits - 1, procs):
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((client_ip, port))
        # max value in /proc/sys/net/core/somaxconn, increase if higher than 128
        sock.listen(128)
        poller.register(sock, READ_ONLY)
        fd_to_socket[sock.fileno()] = sock

    return poller, fd_to_socket


def listener(idx, pipe):
    poller, fd_to_socket = set_up_ports(idx)
    while True:
        readable = poller.poll()
        for ready_server in readable:
            fd, flag = ready_server
            ready_server = fd_to_socket[fd]
            client_port = ready_server.getsockname()[1]
            recv_socket, (server_ip, server_port) = ready_server.accept()
            recv_socket.close()
            pipe.send((client_port, server_port, server_ip))


if procs >= 1:
    proc_arr, (pipe_1, pipe_2) = [], Pipe()
    for idx in range(1, procs + 1):
        proc = Process(target=listener, args=(idx, pipe_1))
        proc_arr.append(proc)
        proc.start()
else:
    poller, fd_to_socket = set_up_ports(1,1)

while not eof_state:
    count = 0
    if verbose:
        step_duration = (time() - start_step)
        kbytes = max_index * bits / 8000
        print ("%.2fkB/s"%(kbytes/step_duration), file=stderr)
        start_step = time()
    while count < max_index:
        port_pairs = []
        if procs and pipe_2.poll():
            while pipe_2.poll():
                count += 1
                client_port, server_port, server_ip = pipe_2.recv()
                port_pairs.append((client_port, server_port))
        elif not procs:
            readable = poller.poll()
            for ready_server in readable:
                count += 1
                fd, flag = ready_server
                ready_server = fd_to_socket[fd]
                client_port = ready_server.getsockname()[1]
                recv_socket, (server_ip, server_port) = ready_server.accept()
                recv_socket.close()
                port_pairs.append((client_port, server_port))

        for client_port, server_port in port_pairs:
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

    print ("".join(bit_buffer))
    if not eof_state:
        bit_buffer = [""] * max_index
        hit_port(0, poll_port)

if procs:
    [proc.terminate() for proc in proc_arr]
