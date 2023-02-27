#!/bin/sh

docker-compose \
    -f docker-compose.yaml \
    -f docker-compose-api-wrapper.yaml \
    -f docker-compose-infrastructure.yaml \
    -f docker-compose-helpers.yaml \
     build "$@"
