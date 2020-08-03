#!/usr/bin/env python2

import argparse
from sys import stdout, stdin
from operator import add

ap = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter, description="", epilog=""
)
ap.add_argument("-i", "--input", default="-", type=str, help="")
args = vars(ap.parse_args())
input_stream = args["input"]

if input_stream == "-":
    raw_file = stdin
else:
    raw_file = open(input_stream, "rb")

bit_array = raw_file.read().split()

if bit_array:
    bits = reduce(add, bit_array)
    for idx in range(int(len(bits) / 8)):
        byte = bits[idx * 8 : (idx + 1) * 8]
        stdout.write(chr(int(byte, 2)))
