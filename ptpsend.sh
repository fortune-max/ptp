#!/bin/bash

# ptpsend $BITS $PIECES $FILE_NAME $CLIENT

ceil (){ CEIL_ANS=$(($(($1+$2-1))/$2)); }

# Obtain file size to det how to break
FILE_SIZE=`ls -l $3 | awk '{print $5}'

# Break file into $PIECES
ceil $FILE_SIZE $2
split -d -b $CEIL_ANS $3

# Launch servers (max 10)
for q in $(seq 1 $2)
do
    CLIENT_OFFSET=$((770+$(($((2**$1))-2))*$q))
    SERVER_OFFSET=$((33734+$(($((2**$1))+10))*$q))
    time python3 ptpserver.py -f x0$(($q-1)) -b $1 -m 99999 -p $((65520+$q)) -o $CLIENT_OFFSET -O $SERVER_OFFSET -c $4 &
done
