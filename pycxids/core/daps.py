# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import jwt
from datetime import datetime
import requests

from pycxids.core import jwt_decode
from pycxids.core.settings import CLIENT_ID, DAPS_ENDPOINT, SCOPE, ASSERTION_TYPE, CONSUMER_CONNECTOR_URL
from pycxids.core.settings import settings

MINIMUM_TOKEN_VALIDITY_SECONDS = 10
_last_daps_token = None

def get_daps_access_token(audience: str):
    daps = get_daps_token(audience=audience)
    return daps['access_token']

def get_daps_token(audience: str):
    """
    audience:   Typically the endpoint for which we request the token.
                If not given, we use the (old) env var
    """
    global _last_daps_token
    now = int(datetime.now().timestamp())
    # TODO: Fix this! We need to check for which endpoint before we return an existing, still valid token!
    #if _daps_token_still_valid(_last_daps_token):
    #    return _last_daps_token

    if not audience:
        audience = CONSUMER_CONNECTOR_URL

    daps_claim_set = {
        "@context": "https://w3id.org/idsa/contexts/context.jsonld",
        "@type": "ids:DatRequestToken",
        "sub": CLIENT_ID,
        "iss": CLIENT_ID,
        "aud": DAPS_ENDPOINT,
        "iat": now,
        "nbf": now,
        #"exp": now + 36000,
    }
    private_key= ''
    with open(settings.PRIVATE_KEY_FN, 'br') as f:
        private_key = f.read()
    client_assertion = jwt.encode(daps_claim_set, algorithm='RS256', key=private_key)

    params = {
        'grant_type' : 'client_credentials',
        'scope' : SCOPE,
        'client_assertion_type' : ASSERTION_TYPE,
        'client_assertion' : client_assertion,
        #'resource': CONSUMER_CONNECTOR_URL,
        'resource': audience,
    }

    r = requests.post(DAPS_ENDPOINT, params=params)
    if not r.ok:
        print(f"Could not fetch token. Reason: {r.reason} Content: {r.content}")
        return None
    j = r.json()
    #print(json.dumps(j, indent=4))
    decoded = jwt_decode.decode(j['access_token'])
    decoded_modified = decoded
    decoded_modified['signature'] = decoded['signature'].hex(':')
    with open('daps_token.json', 'w') as f:
        f.write(json.dumps(decoded_modified, indent=4))
    exp = decoded['payload']['exp']
    diff = exp - now
    #print(diff)
    #print(json.dumps(decoded))
    _last_daps_token = j
    return j

def _daps_token_still_valid(token) -> bool:
    """
    If token still valid for 10 seconds, return True, else False
    """
    if not token:
        return False
    decoded = jwt_decode.decode(token['access_token'])
    exp = decoded.get('payload', {}).get('exp', None)
    if not exp:
        return False
    now = datetime.now().timestamp()
    diff = exp - now

    if diff > MINIMUM_TOKEN_VALIDITY_SECONDS:
        return True
    
    return False