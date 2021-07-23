#!/usr/bin/env python3

import socket
import argparse
from multiprocessing import Process, Queue
from doc import serv_doc, bit_map
from sys import stdin, stderr
from math import ceil
from operator import add

def hitter(pqueue):
    while True:
        server_port, client_port = pqueue.get()
        if (server_port == 'DONE'):
            break
        hit_port(server_port, client_port)


def hit_port(server_port, client_port):
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_ip, server_port))
    # print ("Hitting port ", server_port, client_port, file=stderr)
    server_socket.connect((client, client_port))
    server_socket.close()


def resolve_ports(bit_seq, server_is_idx, idx):
    server_port = server_offset + 1 + [0, idx][server_is_idx]
    client_port = client_offset + 1 + [idx, 0][server_is_idx]

    if len(bit_seq) == bits:
        if len(set(bit_seq)) == 1:
            if server_is_idx:
                return resolve_ports(bit_seq, False, idx)
            server_port += max_index + int(bit_seq[0])
        else:
            client_port += int(bit_seq, 2) - 1
    else:
        if server_is_idx:
            return resolve_ports(bit_seq, False, idx)
        global eof_offset
        eof_offset = bits - len(bit_seq) + 1

        resolve_ports(bit_seq.ljust(bits, "0"), True, idx)
        client_port += 1
        server_port += max_index + eof_offset + 1
        print ("Sending EOF-%d" % (eof_offset - 1))
    if procs == 1:
        hit_port(server_port, client_port)
    else:
        pqueue.put((server_port, client_port))


ap = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=serv_doc
)

ap.add_argument("-O","--server_offset",default=34000,type=int,help="Number of ports to step over before mapping offset+1, ..., to indexes. Default 34000 (in case running both server and client on same machine limit clashes)",)
ap.add_argument("-o","--client_offset",default=1024,type=int,help="Number of ports to step over before mapping offset+1, ..., to bit sequences. Default 1024 (running non-root)",)
ap.add_argument("-m","--max_index",default=248,type=int,help="Number of bit-sequences to send before waiting for acknowledgment from client",)
ap.add_argument("-b","--bits",default=8,type=int,help="Bit space assigned to each port. Default 8 bits",)
ap.add_argument("-f", "--file", default="-", type=str, help="Input file to serve. Default stdin")
ap.add_argument("-i","--ip",default="0.0.0.0",type=str,help="IP address of this machine. Default 0.0.0.0",)
ap.add_argument("-c","--client",default="127.0.0.1",type=str,help="Client IP to serve file to. Default localhost",)
ap.add_argument("-p","--poll_port",default=65535,type=int,help="Port to hit server on to receive next set of bits. Default 65535",)
ap.add_argument("-P","--procs",default=1,type=int,help="How many processes to spawn to speed up transfer. Default 1",)
args = vars(ap.parse_args())

client = args["client"]
input_stream = args["file"]
server_ip = args["ip"]
poll_port = args["poll_port"]
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

if input_stream == "-":
    bytes = stdin
else:
    bytes = open(input_stream, "rb")

chunksize = int(max_index / 8) * bits
eof_offset = -1
idx = 0
# Set up server-poll socket
wait_socket = socket.socket()
wait_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
wait_socket.bind((server_ip, poll_port))
wait_socket.listen(128)


def proc_fn(idxes, bit_seq):
    for idx in idxes:
        to_send = bit_seq[idx * bits : (idx + 1) * bits]
        resolve_ports(to_send, True, idx)

if procs > 1:
    pqueue = Queue()
    for proc in range(procs):
        Process(target=hitter, args=((pqueue),)).start()

while True:
    chunks = bytes.read(chunksize)
    if not chunks:
        break
    bit_seq = "".join([bit_map[x] for x in chunks])
    segments = min(max_index, int(ceil(len(bit_seq) / bits)))
    for idx in range(segments):
        to_send = bit_seq[idx * bits : (idx + 1) * bits]
        resolve_ports(to_send, True, idx)
    # Wait for client ACK if not finished
    if segments == max_index:
        idx = -1  # Assert (idx + 2) % max_index is next index
        while True:
            recv_socket, (recv_ip, recv_port) = wait_socket.accept()
            if recv_ip == client:
                break

# Handle EOF-0 when no rstrip was needed
if eof_offset == -1:
    print ("Sending EOF-0")
    client_port = client_offset + (idx + 2) % max_index
    server_port = server_offset + max_index + 3
    hit_port(server_port, client_port)
wait_socket.close()
pqueue.put(("DONE", None))
print ("Done!")
