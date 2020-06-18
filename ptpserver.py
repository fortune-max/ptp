import socket
import argparse
from sys import stdin
from operator import add
from time import sleep

# Port Legend EOF-0, EOF-1, ..., EOF-14, bit 0, bit 1, bit 10, ..., bit X

DELAY = 0.2  # seconds

ap = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter, description=" ", epilog=" "
)
ap.add_argument("-o", "--offset", default=1024, type=int, help="")
ap.add_argument("-b", "--bits", default=8, type=int, help="")
ap.add_argument("-i", "--input", default="-", type=str, help="")
ap.add_argument("-c", "--client", default="127.0.0.1", type=str, help="")
args = vars(ap.parse_args())
bits, offset, input_stream, client = (
    args["bits"],
    args["offset"],
    args["input"],
    args["client"],
)


def transform_to_port(bit_seq):
    rstrip = bits - len(bit_seq) + 1
    denary = int(bit_seq, 2)
    port_num = denary + offset + 16
    if rstrip > 1:
        global eof_offset
        eof_offset = rstrip
    return port_num


if input_stream == "-":
    bytes = stdin
else:
    bytes = open(input_stream, "rb")

chunksize = 8 * bits
eof_offset = 1

while True:
    chunks = bytes.read(chunksize)
    if not chunks:
        break
    bit_seq = reduce(add, map(lambda x: bin(ord(x))[2:].zfill(8), chunks))
    while bit_seq:
        to_send, bit_seq = bit_seq[:bits], bit_seq[bits:]
        pri_port = transform_to_port(to_send)
        sock = socket.socket()
        print ("Hitting port " + str(pri_port))
        print ("sending " + chunks)
        sock.connect((client, pri_port))
        sock.close()
        sleep(DELAY)

sock = socket.socket()
print ("Finalizing port " + str(offset + eof_offset))
print "EOF-%d" % eof_offset
sock.connect((client, offset + eof_offset))
sock.close()
if eof_offset != 1:
    sleep(DELAY)
    sock = socket.socket()
    print ("refinalizing port " + str(offset + 1))
    print "EOF-0"
    sock.connect((client, offset + 1))
sock.close()
