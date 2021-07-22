#!/usr/bin/env python3

import argparse
from operator import add
from functools import reduce
from sys import stdout, stdin

ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("-i", "--input", default="-", type=str, help="File to encode/decode. Defaults to stdin")
ap.add_argument("-m", "--mode", default="decode", type=str, help="Convert file to bitsequence (encode) or from bitsequence (decode)")
ap.add_argument("-c", "--chunksize",  default=10000000, type=int, help="Num of bytes to translate at a time. Default 10000000 (10MB)")
args = vars(ap.parse_args())
mode, input_stream, chunksize  = args["mode"], args["input"], args["chunksize"]

if input_stream == "-":
    raw_file = stdin.buffer.raw
else:
    raw_file = open(input_stream, "rb")

if mode == "encode":
    while True:
        chunks = raw_file.read(chunksize)
        if not chunks:
            break
        bit_seq = reduce(add, map(lambda x: bin(x)[2:].zfill(8), chunks))
        stdout.write(bit_seq)

else:
    # TODO don't load everything in memory, apply chunks
    bit_array = raw_file.read().split()
    if bit_array:
        bits = reduce(add, bit_array)
        for idx in range(int(len(bits) / 8)):
            byte = bits[idx * 8 : (idx + 1) * 8]
            stdout.buffer.write(bytes([int(byte, 2)]))

