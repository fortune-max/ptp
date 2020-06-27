#!/bin/bash

# ptprecv $BITS $PIECES $FILE_NAME

for q in $(seq 1 $2)
do
    CLIENT_OFFSET=$((1024+$(($((2**$1))-2))*$(($q-1))))
    SERVER_OFFSET=$((34000+$(($((2**$1))+10))*$(($q-1))))
    time python3 ptpclient.py -b $1 -m 99999 -p 6552$q -o $CLIENT_OFFSET -O $SERVER_OFFSET > $30$(($q-1)) &
done
