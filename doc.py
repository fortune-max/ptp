serv_doc="""
This utility sends files from server device (this machine) to a specified client device on which an instance of ptpclient is running.

Useful when you wish to communicate with another device which you can hit it's ports but cannot write data to same port and/or vice versa.
Could also double for making sure your communication with client device is indecipherable/uninterceptable.

Each socket connection (of which there are several) is represented like this:

Socket Server-Side (localhost, server_port) => Socket Client-Side (client_IP, client_port)

For each socket connection, the server hits a listening ${client_port} on specified ${client_IP} with it's own socket running on ${server_port} sending a bit-sequence ${bits} characters long. The bit-sequence is inferred client-side from the value of ${client_port} hit, and the position of the bit-sequence in bit stream data is inferred from the value of ${server_port}.

Values of server_port are selected using the legend, with ${server_offset}+1 mapped to first item and so on:
index 1, index 2, index 3, ..., index ${max_index}, binary(0), binary(2^${bits}-1), EOF-0, EOF-1, ..., EOF-15

Values of client_port are selected using the legend, with ${client_offset}+1 mapped to first item and so on:
binary(1), binary(2), ..., binary(2^${bits}-2)           [binary sequences are zero-filled to length ${bits}]

Some server ports represent something other than indexes:
The EOF bits are sent at the end of the broadcast to know how many bits to right strip from received data. EOF-4 means strip off last 4 bits from sequence then terminate listening on client as all data has been received.
The null bit is also sent from server-side as it cannot be squeezed into the client port when ${bits} value is 16.
The last bit-sequence in bit-space is also sent from server side, as port ${poll_port} is reserved for polling server (to avoid clash when ${bits} is 16)

Each time the server sends the next set of ${max_index} bit-sequences, it waits by listening on port ${poll_port} for the client to state it has received, processed and properly ordered all bit-sequences received, using the accompanying indexes inferred from ${server_port}. The next set of ${max_index} bit-sequences are then sent and the process repeated till completion. This is to prevent ambiguity in where to position bits and ensure the transfer runs as quickly as (possibly varying) network speeds allow."""
