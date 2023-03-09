#!/bin/sh
# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


mkdir -p ./demokeys

# CA: -x509 creates a self-signed certificate. Can also be used as a CA certificate
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -subj "/CN=ca1.localdomain" \
    -keyout ./demokeys/ca_1.key -out ./demokeys/ca_1.crt
openssl x509 -in ./demokeys/ca_1.crt -text -noout > ./demokeys/ca_1.crt.txt

# client_1: without -x509 creates the csr
openssl req -newkey rsa:2048 -new -nodes -subj "/CN=client1.localdomain" \
    -keyout ./demokeys/client_1.key -out ./demokeys/client_1.csr


# cross-sign the client certificate with the CA certificate/key
openssl x509 -CA ./demokeys/ca_1.crt -CAkey ./demokeys/ca_1.key \
    -CAcreateserial -days 365 \
    -req -in ./demokeys/client_1.csr -out ./demokeys/client_1.crt
openssl x509 -in ./demokeys/client_1.crt -text -noout > ./demokeys/client_1.crt.txt

# openssl verify -verbose -CAfile ./demokeys/ca_1.crt ./demokeys/client_1.crt
# openssl req -in ./demokeys/client_1.csr  -text
# openssl x509 -in ./demokeys/client_1.crt -text

# now a second CA and client_2
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -subj "/CN=ca2.localdomain" \
    -keyout ./demokeys/ca_2.key -out ./demokeys/ca_2.crt
openssl x509 -in ./demokeys/ca_2.crt -text -noout > ./demokeys/ca_2.crt.txt

openssl req -newkey rsa:2048 -new -nodes -subj "/CN=client2.localdomain" \
    -keyout ./demokeys/client_2.key -out ./demokeys/client_2.csr

openssl x509 -CA ./demokeys/ca_2.crt -CAkey ./demokeys/ca_2.key \
    -CAcreateserial -days 365 \
    -req -in ./demokeys/client_2.csr -out ./demokeys/client_2.crt
openssl x509 -in ./demokeys/client_2.crt -text -noout > ./demokeys/client_2.crt.txt
