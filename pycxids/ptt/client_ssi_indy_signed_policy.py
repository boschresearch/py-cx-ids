# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
import base58
import requests
import jwt

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

SEED_INSECURE = os.getenv('SEED_INSECURE', 'Eek7aejoo5aeRoleichooGhoh5Kei8ne')
assert len(SEED_INSECURE) == 32, "SEED_INSECURE must be 32 characters!"

SEED2_INSECURE = os.getenv('SEED2_INSECURE', 'IeCah3ken5ou9ootooYu1uuv9yeeth6x')
assert len(SEED2_INSECURE) == 32, "SEED2_INSECURE must be 32 characters!"

REGISTER_DID_ENDPOINT = os.getenv('REGISTER_DID_ENDPOINT', 'http://test.bcovrin.vonx.io/register')
POLICY = 'http://localhost:8080/policy/cdfd26aaf5b1fdc6d71af7c1349869f9314b67626bc1eec44e64af674e357eed'

data = {
    "role": "ENDORSER",
    "seed": SEED_INSECURE,
}
# SECURITY: as the name 'SEED_INSECURE', the seed / secret is UNSECURE because we post it here to another server!
r = requests.post(REGISTER_DID_ENDPOINT, json=data)

assert r.ok, f"Could not create DID on the ledger {REGISTER_DID_ENDPOINT}"

j = r.json()
did_in_namespace = j.get('did')
did = f"did:indy:bcgov:test:{did_in_namespace}" # TODO
verkey = j.get('verkey') # aka public key

private_key = Ed25519PrivateKey.from_private_bytes(SEED_INSECURE.encode())
public_key = private_key.public_key()
pk_raw = public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
print(pk_raw)
pk_b58 = base58.b58encode(pk_raw)
print(pk_b58)

assert verkey == pk_b58.decode(), "The public key that we calculated locally does not match the one we received (verkey) from the ledger."

r = requests.head('http://localhost:8080/abc/xxx')

assert r.ok, "Could not fetch HEAD request / policy"
policy = r.headers.get('policy')

assert policy, "Could not fetch policy from server"

claims = {
    'policy': policy,
}

jwt_headers = {
    'alg': 'EdDSA',
    'crv': 'Ed25519',
    'kid': did,
}

policy_token = jwt.encode(claims, key=private_key, headers=jwt_headers, algorithm='EdDSA')

headers = {
    'Policy': policy_token
}

r = requests.get("http://localhost:8080/requiresSSIsignedpolicy", headers=headers)

assert r.ok, "Could not fetch data from SSI protected endpoint"

print(r.content)

# now sign with another key to check if acces is NOT granted
private_key2 = Ed25519PrivateKey.from_private_bytes(SEED2_INSECURE.encode())
policy_token = jwt.encode(claims, key=private_key2, headers=jwt_headers, algorithm='EdDSA')

headers = {
    'Policy': policy_token
}

r = requests.get("http://localhost:8080/requiresSSIsignedpolicy", headers=headers)

assert r.status_code == 403, "Access should be denied with a wrongly signed key"
