#!/bin/sh

docker-compose -f docker-compose-infrastructure.yaml -f docker-compose-helpers.yaml \
    down --volumes
docker-compose -f docker-compose-infrastructure.yaml -f docker-compose-helpers.yaml \
    up --force-recreate vault db daps-mock receiver-service third-receiver-service provider-receiver-service dummy-backend \
    consumer-webhook-service third-webhook-service adminer
