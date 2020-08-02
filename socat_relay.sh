#!/bin/bash

MODE=$1
FWD_TO_IP=$2
FWD_TO_PORT=$3
FWD_SOURCE_PORT=${SOCAT_PEER_PORT}

if [ $MODE = "UDP" ];then
    socat UDP:${FWD_TO_IP}:${FWD_TO_PORT},sp=${SOCAT_PEERPORT},reuseaddr SYSTEM:"echo p"
elif [ $MODE = "TCP" ];then
    socat TCP:${FWD_TO_IP}:${FWD_TO_PORT}, SYSTEM:"echo p"
fi
