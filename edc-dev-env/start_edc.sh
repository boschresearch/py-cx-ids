#!/bin/sh

docker-compose -f docker-compose.yaml down --volumes
docker-compose -f docker-compose.yaml up --force-recreate \
   provider-data-plane provider-control-plane \
   consumer-control-plane
