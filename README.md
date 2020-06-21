# ptp
Port-to-Port Protocol for sending files through hitting ports

Overview
===
This utility sends files from server device (your machine) to a specified client device on which an instance of ptpclient is running.

Useful when you wish to communicate with another device which you can hit it's ports but cannot write data to same port and/or vice versa (this is the case when you're using mobile data and have no more balance, can hit endpoints but can't transmit data across these ports but this works around that).  

Could also double for making sure your communication with client device is indecipherable/uninterceptable.

Each socket connection (of which there are several) is represented like this:

**Socket Server-Side (localhost, server port) => Socket Client-Side (client IP, client port)**

For each socket connection, the server hits a listening ${client port} on specified ${client IP} with it's own socket running on ${server port} sending a bit-sequence ${bits} characters long. 

The bit-sequence is inferred client-side from the value of ${client port} hit, and the position of the bit sequence in bit stream data is inferred from the value of ${server port}.

Legend
===

Values of server port are selected using the legend, with ${server offset}+1 mapped to first item and so on:  

**index 1, index 2, index 3, ..., index ${max index}, binary(0), binary(2^${bits}-1), EOF-0, EOF-1, ..., EOF-15**

Values of client port are selected using the legend, with ${client offset}+1 mapped to first item and so on:  

**binary(1), binary(2), ..., binary(2^${bits}-2)           [binary sequences are zero-filled to length ${bits}]**

Some server ports represent something other than indexes:  

The EOF bits are sent at the end of the broadcast to know how many bits to right strip from received data.  

EOF-4 means strip off last 4 bits from sequence then terminate listening on client as all data has been received.

The null bit is also sent from server-side as it cannot be squeezed into the client port when ${bits} value is 16.

The last bit-sequence in bit-space is also sent from server side, as port 65535 is reserved for polling server (to avoid clash when ${bits} is 16)

Each time the server sends the next set of ${max index} bit-sequences, it waits by listening on port 65535 for the client to state it has received, processed and properly ordered all bit-sequences received, using the accompanying indexes inferred from ${server port}. The next set of ${max index} bit-sequences are then sent and the process repeated till completion. This is to prevent ambiguity in where to position bits and ensure the transfer runs as quickly as (possibly varying) network speeds allow.


Usage
===
**Server-side**
> python2 ptpserver.py -i /path/to/file -c <client IP>  
  
or  
> cat /path/to/file | python2 ptpserver.py -c <client IP>

**Client-side**
> python2 ptpclient.py | tee outfile
