import socket
import argparse
import select
from sys import stderr


# READ_ONLY = (
#     select.POLLIN | select.POLLPRI | select.POLLPRI | select.POLLHUP | select.POLLERR
# )
# READ_WRITE = READ_ONLY | select.POLLOUT

# Legend EOF-0, EOF-1, ..., EOF-14, bit 0, bit 1, bit 10, ..., bit X

ap = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter, description=" ", epilog=" "
)
ap.add_argument("-o", "--offset", default=1024, type=int, help="")
ap.add_argument("-b", "--bits", default=8, type=int, help="")
args = vars(ap.parse_args())
bits, offset = args["bits"], args["offset"]


def handle_port(port):
    print >> stderr, "Handling port", port
    port -= offset
    if port <= 15:
        # Handle EOF
        port -= 1
        return -port
    else:
        port -= 16
        return bin(port)[2:].zfill(bits)


port_array = []

for port in range(1 + offset, 15 + 2 ** bits + offset + 1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(1)
    port_array.append(sock)

while True:
    # poller = select.poll()
    # poller.register(server, READ_ONLY)
    readable, _, _ = select.select(port_array, [], [])
    ready_server = readable[0]
    recv_socket, (recv_ip, recv_port) = ready_server.accept()
    result = handle_port(ready_server.getsockname()[1])
    if result == 0:
        break
    print(result)
    recv_socket.close()
