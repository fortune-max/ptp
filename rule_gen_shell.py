#!/usr/bin/env python3
base_tcp = "socat TCP4-LISTEN:%d,fork TCP4:%s:%d &"
base_udp = "socat UDP4-LISTEN:%d,fork UDP4-SENDTO:%s:%d &"
bits = 8
rule_id = 0
client_offset = 1024
server_offset = 34000
max_idx = 2**bits - 8
ip = "192.168.43.45"
mode="client" # server and/or client rules

if "server" in mode:
  for port in range(server_offset + 1, server_offset + max_idx + 18 + 1):
    # bits 8, range(34001, 34267) [266]
    tmplt = (port, ip, port)
    print (base_tcp % tmplt)

if "client" in mode:
  for port in range(client_offset + 1, client_offset + 2**bits-1):
    # bits 8, range(1025, 1279) [254]
    tmplt = (port, ip, port)
    print( base_udp % tmplt)
  port = 65535
  tmplt = (port, ip, port)
  print (base_tcp % tmplt)
