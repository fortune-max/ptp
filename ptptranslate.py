import argparse
from sys import stdout

ap = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter, description=" ", epilog=" "
)
ap.add_argument("-i", "--input", default="-", type=str, help="")
args = vars(ap.parse_args())
input_stream = args["input"]

if input_stream == "-":
    bytes = stdin
else:
    bytes = open(input_stream, "rb")

while True:
    byte = bytes.read(9).strip()
    if not byte:
        break
    stdout.write(chr(int(byte, 2)))
