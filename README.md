# ptp
Port-to-Port Protocol for sending files through hitting ports

Overview
===
The utility, ptpserver.py, sends files from server device (your machine) to a specified client device on which an instance of ptpclient.py is running.

Useful when you wish to communicate with another device which you can hit it's ports but cannot write data to same ports and/or vice versa (this is the case when you're using mobile data and have no more balance, can hit endpoints but can't transmit data across these ports but this works around that).  

Could also double for making sure your communication with client device is indecipherable/uninterceptable.

Each socket connection (of which there are several) is represented like this:

**Socket Server-Side (localhost, server port) => Socket Client-Side (client IP, client port)**

For each socket connection, the server hits a listening ${client port} on specified ${client IP} with it's own socket bound to ${server port} sending a bit-sequence ${bits} characters long. 

The bit-sequence is inferred client-side from the value of ${client port} hit, and the position of the bit sequence in bit stream data is inferred from the value of ${server port}.

Legend
===

Values of server port are selected using the legend, with ${server offset}+1 mapped to first item and so on:  

**index 1, index 2, index 3, ..., index ${max index}, binary(0), binary(2^{bits}-1), EOF-0, EOF-1, ..., EOF-15**

Values of client port are selected using the legend, with ${client offset}+1 mapped to first item and so on:  

**binary(1), binary(2), ..., binary(2^{bits}-2)           [binary sequences are left-padded with zeroes to length ${bits}]**

Some server ports represent something other than indexes:  

The EOF bits are sent at the end of the broadcast to know how many bits to right strip from received data.  

EOF-4 means strip off last 4 bits from sequence then terminate listening on client as all data has been received.

The null bit-sequence (all zeros) and last bit-sequence in bit-space (all ones) are also sent from server-side.

Each time the server sends the next set of ${max index} bit-sequences, it waits for the client to state it has received, processed and properly ordered all bit-sequences received, using the accompanying indexes inferred from ${server port}. Any indexes missing are re-queried by client and resent by server till all ${max index} bit-sequences are accounted for client-side. The next set of ${max index} bit-sequences are then sent and the process repeated till completion. This is to prevent ambiguity in where to position bits and ensure the transfer runs as quickly as (possibly varying) network speeds allow.


Usage
===
#### Important
Ensure to run client before server.  
Parameters common to both client and server must be the same for both when run (bits, offsets, max index).

#### Running on same machine (testing, etc)  

_Terminal 1 (acting as client and run first)_
> ./ptpclient.py | ./ptptranslate.py > outfile

_Terminal 2 (acting as server and serves a file  to client)_  
> ./ptpserver.py -f testfiles/hightail.conf  

#### Different Server & Client machine  

**Client-side**
> ./ptpclient.py | ./ptptranslate.py > outfile

**Server-side**
> ./ptpserver.py -f /path/to/file -c client_ip  
