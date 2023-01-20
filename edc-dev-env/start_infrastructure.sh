#!/bin/sh

docker-compose -f docker-compose-infrastructure.yaml up --force-recreate vault db daps-mock
