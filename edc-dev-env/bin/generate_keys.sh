#!/bin/sh

# Provider
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -subj "/CN=localhost.localdomain" -keyout ./vault_secrets/provider.key -out ./vault_secrets/provider.crt
# EDC token encryption keys
key1=`openssl rand -base64 16`
key2=`openssl rand -base64 24`
key3=`openssl rand -base64 32`
echo "${key1},${key2},${key3}" > ./vault_secrets/provider-encryption.keys

# Consumer
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -subj "/CN=localhost.localdomain" -keyout ./vault_secrets/consumer.key -out ./vault_secrets/consumer.crt
# EDC token encryption keys
key1=`openssl rand -base64 16`
key2=`openssl rand -base64 24`
key3=`openssl rand -base64 32`
echo "${key1},${key2},${key3}" > ./vault_secrets/consumer-encryption.keys

# Third
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -subj "/CN=localhost.localdomain" -keyout ./vault_secrets/third.key -out ./vault_secrets/third.crt
# EDC token encryption keys
key1=`openssl rand -base64 16`
key2=`openssl rand -base64 24`
key3=`openssl rand -base64 32`
echo "${key1},${key2},${key3}" > ./vault_secrets/third-encryption.keys

# DAPS
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -subj "/CN=localhost.localdomain" -keyout ./daps-mock/daps.key -out ./daps-mock/daps.crt
