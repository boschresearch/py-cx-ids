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


# first, try to get the content
url = f"http://localhost:8080/requiressignedpolicy"

r = requests.get(url)

if not r.ok:
    # we expect this
    print(f"reason: {r.reason} content: {r.content}")


# now let's fetch the policy information from the header
r = requests.head(url)

if not r.ok:
    print(f"reason: {r.reason} content: {r.content}")
    sys.exit()

policy = r.headers.get('policy')
if not policy:
    sys.exit()

# now get the policy indirectly signed, by sending it to the DAPS
# to make it part of the token
daps_token = get_daps_token(audience=policy)


access_token = daps_token['access_token']

headers = {
    'Policy': access_token
}

r = requests.get(url, headers=headers)

if not r.ok:
    print(f"reason: {r.reason} content: {r.content}")
    sys.exit()

print(r.content)

# the usage policy is given in the header
# for simplicity, we don't check it here anymore (see other client for details)
