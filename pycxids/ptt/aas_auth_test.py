# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import time
import json
import uuid
import base64
import requests
import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

PRIVATE_KEY_FN = os.getenv('PRIVATE_KEY_FN', './pycxids/ptt/demokeys/client_1.key')
CERTIFICATE_FN = os.getenv('CERTIFICATE_FN', './pycxids/ptt/demokeys/client_1.crt')

TOKEN_ENDPOINT = os.getenv('TOKEN_ENDPOINT', 'https://admin-shell-io.com/50001/connect/token')

certificate_data = ''
with open(CERTIFICATE_FN, 'rb') as f:
    certificate_data = f.read()

certificate = x509.load_pem_x509_certificate(data=certificate_data)

# prepare our certificates and key
private_key = ''
with open(PRIVATE_KEY_FN, 'rb') as f:
    private_key = f.read()

now = int(time.time())

payload = {
    'iss': 'client.jwt',
    'sub': 'client.jwt',
    'aud': TOKEN_ENDPOINT,
    'user': 'myname@company.org',
    'jti': str(uuid.uuid4()),
    'iat': now,
    'nbf': now,
    'exp': now+1800,
}

# according to the spec, it is a lis tof b64 (not urlsafe!) encoded certs. signing cert is first
der = certificate.public_bytes(encoding=serialization.Encoding.DER)
der_b64 = base64.b64encode(der)
x5c = [
    der_b64.decode()
]

jwt_headers = {
    'typ': 'JWT',
    'x5c': x5c,
    'alg': 'RS256'
}

client_assertion = jwt.encode(payload=payload, algorithm='RS256', key=private_key, headers=jwt_headers)

decoded = jwt.decode(jwt=client_assertion, algorithms=['RS256'], options={'verify_signature': False})

print(json.dumps(decoded, indent=4))

params = {
    'grant_type' : 'client_credentials',
    'scope' : 'resource1.scope1',
    'client_assertion_type' : "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    'client_assertion' : client_assertion,
    #'client_id': 'client1',
}
headers = {
    'Accept': 'application/json',
    'Content-type': 'application/x-www-form-urlencoded',
}

r = requests.post(TOKEN_ENDPOINT, params=params, headers=headers)

if not r.ok:
    print(f"reason: {r.reason} content: {r.content}")
    sys.exit()

j = r.json()
print(json.dumps(j, indent=4))

assert j['access_token']