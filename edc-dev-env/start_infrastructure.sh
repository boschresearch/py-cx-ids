#!/bin/sh

docker-compose -f docker-compose-infrastructure.yaml -f docker-compose-helpers.yaml \
    down --volumes
docker-compose -f docker-compose-infrastructure.yaml -f docker-compose-helpers.yaml \
    up --force-recreate vault db receiver-service dummy-backend \
    adminer dsp-consumer cx-services-mocks
