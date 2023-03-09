# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import hashlib
import base64
from urllib.parse import urlparse
import requests
import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

PRIVATE_KEY_FN = os.getenv('PRIVATE_KEY_FN', './pycxids/ptt/demokeys/client_1.key')
CERTIFICATE_FN = os.getenv('CERTIFICATE_FN', './pycxids/ptt/demokeys/client_1.crt')

PRIVATE_KEY_FN_2 = os.getenv('PRIVATE_KEY_FN_2', './pycxids/ptt/demokeys/client_2.key')
CERTIFICATE_FN_2 = os.getenv('CERTIFICATE_FN_2', './pycxids/ptt/demokeys/client_2.crt')


base_url = 'http://localhost:8080'
url = f"{base_url}/requiresx509casignedpolicy"

certificate_data = ''
with open(CERTIFICATE_FN, 'rb') as f:
    certificate_data = f.read()

certificate = x509.load_pem_x509_certificate(data=certificate_data)


# basic checks before we start
CA_CERTIFICATE_FN = "./pycxids/ptt/demokeys/ca_1.crt"
ca_cert_data = ''
with open(CA_CERTIFICATE_FN, 'rb') as f:
    ca_cert_data = f.read()
ca_certificate = x509.load_pem_x509_certificate(ca_cert_data)
ca_pub_key = ca_certificate.public_key()
try:
    ca_pub_key.verify(certificate.signature, certificate.tbs_certificate_bytes, algorithm=hashes.SHA256(), padding=padding.PKCS1v15())
except Exception as ex:
    print(ex)


r = requests.get(url)

assert r.ok == False, "We should not be able to get data without providing a signed policy."


# now let's fetch the policy information from the header
r = requests.head(url)

assert r.ok, "Could not fetch policy via http HEAD request"

policy = r.headers.get('policy')

assert policy, "No policy in fetched header"

# prepare our certificates and key
private_key = ''
with open(PRIVATE_KEY_FN, 'rb') as f:
    private_key = f.read()


claims = {
    'policy': policy,
}

# according to the spec, it is a lis tof b64 (not urlsafe!) encoded certs. signing cert is first
der = certificate.public_bytes(encoding=serialization.Encoding.DER)
der_b64 = base64.b64encode(der)
x5c = [
    der_b64.decode()
]

jwt_headers = {
    'x5c': x5c,
    'alg': 'RS256'
}

policy_token = jwt.encode(claims, algorithm='RS256', key=private_key, headers=jwt_headers)

headers = {
    'Policy': policy_token
}

r = requests.get(url, headers=headers)

if not r.ok:
    print(f"reason: {r.reason} content: {r.content}")
    sys.exit()

content = r.content
#print(content)
assert content, "Content must not be empty"

# the usage policy is given in the header
# for simplicity, we don't check it here anymore (see other client for details)

# and now, sign with another key to check if it fails as it should

# prepare our certificates and key
private_key = ''
with open(PRIVATE_KEY_FN_2, 'rb') as f:
    private_key = f.read()

certificate_2_data = ''
with open(CERTIFICATE_FN_2, 'rb') as f:
    certificate_2_data = f.read()
certificate_2 = x509.load_pem_x509_certificate(certificate_2_data)
der = certificate_2.public_bytes(encoding=serialization.Encoding.DER)
der_b64 = base64.b64encode(der)
x5c = [
    der_b64.decode()
]
jwt_headers['x5c'] = x5c # contains the certificate signed with with wrong CA
policy_token_unregistered = jwt.encode(claims, algorithm='RS256', key=private_key, headers=jwt_headers)
headers = {
    'Policy': policy_token_unregistered
}

r = requests.get(url, headers=headers)

assert r.status_code == 403, "Access should be forbidden with a wrongly signed policy"
