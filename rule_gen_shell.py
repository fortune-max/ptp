#!/usr/bin/env python3
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("-i","--ip",type=str,help="IP address of this machine",)
ap.add_argument("-b","--bits",default=8,type=int,help="Bit space assigned to each port. Default 8 bits",)
ap.add_argument("-O","--server_offset",default=34000,type=int,help="Number of ports to step over before mapping offset+1, ..., to indexes. Default 34000 (in case running both server and client on same machine limit clashes)",)
ap.add_argument("-o","--client_offset",default=1024,type=int,help="Number of ports to step over before mapping offset+1, ..., to bit sequences. Default 1024 (running non-root)",)
ap.add_argument("-p","--port_offset",type=int,help="socat bound ports offseted by this amount from source port. Defaults to max index+18",)
ap.add_argument("-P","--poll_offset",type=int,help="socat bound poll port offseted by this amount from source poll port. Defaults to -1",)
ap.add_argument("-m","--max_index",type=int,help="Number of bit-sequences to send before waiting for acknowledgment from client",)
ap.add_argument("-s", "--server_mode", action="store_true", help="Generate forward-to-server scripts")
ap.add_argument("-c", "--client_mode", action="store_true", help="Generate forward-to-client scripts")

args = vars(ap.parse_args())

base_tcp = "socat TCP4-LISTEN:%d,fork TCP4:%s:%d,sp=%d &"
base_poll = "socat TCP4-LISTEN:%d,fork TCP4:%s:%d,sp=%d &"
base_udp = "socat UDP4-LISTEN:%d,fork UDP4-SENDTO:%s:%d,sp=%d &"

bits = args["bits"]
client_offset = args["client_offset"]
server_offset = args["server_offset"]
port_offset = args["port_offset"] or (2**bits + 10)
poll_offset = args["poll_offset"] or -1
ip = args["ip"]
if not ip:
    ip = input("Enter target IP: ")
server_mode = args["server_mode"]
client_mode = args["client_mode"]
max_idx = args["max_index"] or (2**bits - 8)

if server_mode:
  for port in range(server_offset + 1, server_offset + max_idx + 18 + 1):
    # bits 8, range(34001, 34267) [266]
    offseted_port = port + port_offset
    tmplt = (offseted_port, ip, port, port)
    print (base_tcp % tmplt)

elif client_mode:
  for port in range(client_offset + 1, client_offset + 2**bits-1):
    # bits 8, range(1025, 1279) [254]
    offseted_port = port + port_offset
    tmplt = (offseted_port, ip, port, port)
    print( base_udp % tmplt)
  port = 65535
  offseted_port = port + poll_offset
  tmplt = (offseted_port, ip, port, port)
  print (base_poll % tmplt)
