#!/bin/sh

docker-compose -f docker-compose-infrastructure.yaml up vault db daps-mock
