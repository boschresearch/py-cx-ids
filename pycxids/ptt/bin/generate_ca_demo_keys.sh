#!/bin/sh
# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


mkdir -p .secrets

# CA: -x509 creates a self-signed certificate. Can also be used as a CA certificate
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -subj "/CN=localhost.localdomain" \
    -keyout .secrets/ca_1.key -out .secrets/ca_1.crt

# client_1: without -x509 creates the csr
openssl req -newkey rsa:2048 -new -nodes -days 3650 -subj "/CN=localhost.localdomain" \
    -keyout .secrets/client_1.key -out .secrets/client_1.csr


# cross-sign the client certificate with the CA certificate/key
openssl x509 -CA .secrets/ca_1.crt -CAkey .secrets/ca_1.key \
    -CAcreateserial -days 365 \
    -req -in .secrets/client_1.csr -out .secrets/client_1.crt


# openssl req -in .secrets/client_1.csr  -text
# openssl x509 -in .secrets/client_1.crt -text

# now a second CA and client_2
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -subj "/CN=localhost.localdomain" \
    -keyout .secrets/ca_2.key -out .secrets/ca_2.crt

openssl req -newkey rsa:2048 -new -nodes -days 3650 -subj "/CN=localhost.localdomain" \
    -keyout .secrets/client_2.key -out .secrets/client_2.csr

openssl x509 -CA .secrets/ca_2.crt -CAkey .secrets/ca_2.key \
    -CAcreateserial -days 365 \
    -req -in .secrets/client_2.csr -out .secrets/client_2.crt
