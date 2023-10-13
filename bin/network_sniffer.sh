#!/bin/sh

IP=`docker network inspect edc-dev-env_default | jq -r '.[0].IPAM.Config[0].Gateway'`
echo $IP

INTERFACE=`ifconfig | grep -B1 $IP | head -1 | awk -F ':' '{print $1}'`
echo $INTERFACE

sudo httpry -i $INTERFACE -F -b network.dump tcp
