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
from cryptography.hazmat.primitives import hashes

PRIVATE_KEY_FN = os.getenv('PRIVATE_KEY_FN', './edc-dev-env/vault_secrets/consumer.key')
CERTIFICATE_FN = os.getenv('CERTIFICATE_FN', './edc-dev-env/vault_secrets/consumer.crt')

PRIVATE_KEY_FN_UNREGISTERED = os.getenv('PRIVATE_KEY_FN_UNREGISTERED', './edc-dev-env/vault_secrets/provider.key')


base_url = 'http://localhost:8080'
url = f"{base_url}/requiresx509signedpolicy"
certificate_upload_url = f"{base_url}/x509upload"


r = requests.get(url)

if not r.ok:
    # we expect this
    #print(f"reason: {r.reason} content: {r.content}")
    pass


# now let's fetch the policy information from the header
r = requests.head(url)

if not r.ok:
    print(f"reason: {r.reason} content: {r.content}")
    sys.exit()

policy = r.headers.get('policy')
if not policy:
    sys.exit()

# prepare our certificates and key
private_key = ''
with open(PRIVATE_KEY_FN, 'rb') as f:
    private_key = f.read()

certificate_data = ''
with open(CERTIFICATE_FN, 'rb') as f:
    certificate_data = f.read()

certificate = x509.load_pem_x509_certificate(data=certificate_data)
fingerprint = certificate.fingerprint(algorithm=hashes.SHA256())
# https://www.rfc-editor.org/rfc/rfc7515#section-4.1.8
fp_encoded = base64.urlsafe_b64encode(fingerprint).rstrip(b"=").decode() # remove padding from the end

# make sure the server knows our certificate - of course, this needs to happen during registration of the client!
# if not x509 pinning is desired, use properly signed certificates and only upload the root CA certificates to the server.
# slightly different, e.g. header information, but very similar flow
r = requests.post(certificate_upload_url, files={ 'certificate': certificate_data })
if not r.ok:
    print(f"Could not upload the x509 certificat to the server. Reason: {r.reason} content: {r.content}")
    sys.exit()



claims = {
    'policy': policy,
}

jwt_headers = {
    'x5t#S256': fp_encoded,
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
print(content)
assert content, "Content must not be empty"

# the usage policy is given in the header
# for simplicity, we don't check it here anymore (see other client for details)

# and now, sign with another key to check if it fails as it should

# prepare our certificates and key
private_key = ''
with open(PRIVATE_KEY_FN_UNREGISTERED, 'rb') as f:
    private_key = f.read()

# signing the same message with this other key

policy_token_unregistered = jwt.encode(claims, algorithm='RS256', key=private_key, headers=jwt_headers)
headers = {
    'Policy': policy_token_unregistered
}

r = requests.get(url, headers=headers)

assert r.status_code == 403, "Access should be forbidden with a wrongly signed policy"
