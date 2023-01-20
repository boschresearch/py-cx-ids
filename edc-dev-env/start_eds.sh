#!/bin/sh

docker-compose -f docker-compose.yaml -f docker-compose-api-wrapper.yaml up provider-data-plane provider-control-plane consumer-data-plane consumer-control-plane api-wrapper
