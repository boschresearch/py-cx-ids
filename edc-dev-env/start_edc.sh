#!/bin/sh

docker-compose -f docker-compose.yaml -f docker-compose-api-wrapper.yaml down --volumes
docker-compose -f docker-compose.yaml up --force-recreate \
   provider-data-plane provider-control-plane \
   consumer-control-plane
