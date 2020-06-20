import socket
import argparse
import select
from sys import stderr
from operator import add


def hit_port(client_port, server_port):
    client_socket = socket.socket()
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.bind(("0.0.0.0", client_port))
    print ("Hitting port " + str(server_port))
    client_socket.connect((server_ip, server_port))
    client_socket.close()


def handle_ports(client_port, server_port):
    # print >> stderr, "Handling port", port
    if server_port > (server_offset + max_index):
        # Handle special case server_port
        server_port -= (server_offset + max_index)
        if server_port == 1:
            bit_seq = '0' * bits
            index = client_port - client_offset - 1
        elif server_port == 2:
            bit_seq = '1' * bits
            index = client_port - client_offset - 1
        else:
            bit_seq = "-%d" % (server_port - 3)
            index = client_port - client_offset - 1
    else:
        # Handle server port as index and client as bit-sequence
        bit_seq = bin(client_port - client_offset)[2:].zfill(bits)
        index = server_port - server_offset - 1
    return (index, bit_seq)


# READ_ONLY = (select.POLLIN | select.POLLPRI | select.POLLPRI | select.POLLHUP | select.POLLERR)
# READ_WRITE = READ_ONLY | select.POLLOUT
# poller = select.poll()
# poller.register(server, READ_ONLY)

ap = argparse.ArgumentParser()

ap.add_argument("-O","--server_offset",default=34000,type=int,help="Number of ports to step over before mapping offset+1, ..., to indexes. Default 34000 (in case running both server and client on same machine limit clashes)")
ap.add_argument("-o","--client_offset",default=1024,type=int,help="Number of ports to step over before mapping offset+1, ..., to bit sequences. Default 1024 (running non-root)",)
ap.add_argument("-m","--max_index",default=248,type=int,help="Number of bit-sequences to send before waiting for acknowledgment from client",)
ap.add_argument("-b","--bits",default=8,type=int,help="Bit space assigned to each port. Default 8 bits",)
args = vars(ap.parse_args())

if args["bits"] < 4:
    print "Minimum bits is 4, using ", 4
elif args["bits"] > 16:
    print "Maximum bits exceeded, using ", 16
bits = max(min(args["bits"], 16), 4)

if args["client_offset"] > 65534 - 2 ** bits + 2:
    print "Client Offset value exceeded, using ", 65534 - 2 ** bits + 2
client_offset = min(args["client_offset"], 65534 - 2 ** bits + 2)

if args["max_index"] > 2 ** bits - 8:
    print "Max index value exceeded, using ", 2 ** bits - 8
elif args["max_index"] % 8:
    print "Max index must be divisible by 8, using ", args["max_index"] / 8 * 8
elif args["max_index"] == 0:
    print "Invalid Max index, using minimum value 8"
max_index = max(min(args["max_index"] / 8 * 8, 2 ** bits - 8), 8)

if args["server_offset"] > 65535 - 19 - max_index:
    print "Server Offset value exceeded, using ", 65535 - 19 - max_index
server_offset = min(args["server_offset"], 65535 - 19 - max_index)


server_ip = None
port_array = []
bit_buffer = [''] * max_index
eof = False

for port in range(client_offset + 1, client_offset + 2 ** bits - 2):
    sock = socket.socket()
    sock.bind(("0.0.0.0", port))
    sock.listen(1)
    port_array.append(sock)

while not eof:
    for count in range(max_index):
        readable, _, _ = select.select(port_array, [], [])
        ready_server = readable[0]
        client_port = ready_server.getsockname()[1]
        recv_socket, (server_ip, server_port) = ready_server.accept()
        recv_socket.close()
        index, bit_seq = handle_ports(client_port, server_port)
        if bit_seq.startswith('-'):
            # Handle EOF
            bit_buffer[index-1] = bit_buffer[index-1][:int(bit_seq)]
            eof = True
            break
        else:
            bit_buffer[index] = bit_seq
    print reduce(add, bit_buffer)
    if not eof:
        hit_port(65534, 65535)
