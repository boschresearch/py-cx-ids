# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import sys
import hashlib
from urllib.parse import urlparse
import requests
from pycxids.core.daps import get_daps_token

POLICY_HEADER = "Policy"

daps_token = get_daps_token(audience='')
#print(daps_token)

access_token = daps_token['access_token']

headers = {
    'Authorization': f"bearer {access_token}"
}

url = f"http://localhost:8080/"
r = requests.get(url, headers=headers)

if not r.ok:
    print(f"reason: {r.reason} content: {r.content}")
    sys.exit()

print(r.content)
# the usage policy is given in the header
policy = r.headers[POLICY_HEADER]
print(policy)

# if we want, we can request the policy
r = requests.get(policy)
print(r.content)

# and even verify the hash matches the received policy
hash_content = hashlib.sha256(r.content).hexdigest()
path = urlparse(policy).path
hash_policy = path.split('/')[-1]

if not hash_content == hash_policy:
    print(f"WARNING: calculate hash from conent: {hash_content} does NOT match hash from Policy sent with data: {hash_policy}")
else:
    print(f"Policy has the same fingerprint / hash as the one referenced in the data transfer.")