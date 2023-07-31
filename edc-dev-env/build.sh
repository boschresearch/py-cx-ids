#!/bin/sh

# enable in case you wan to see more output during the build
#export DOCKER_BUILDKIT=0
#export BUILDKIT_PROGRESS=plain

docker-compose \
    -f docker-compose.yaml \
    -f docker-compose-api-wrapper.yaml \
    -f docker-compose-infrastructure.yaml \
    -f docker-compose-helpers.yaml \
     build "$@"
