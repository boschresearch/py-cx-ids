# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import jwt
from datetime import datetime
import requests

from pycxids.core.ids import IdsBase
from pycxids.core import jwt_decode
from pycxids.core.settings import CLIENT_ID, DAPS_ENDPOINT, SCOPE, ASSERTION_TYPE, CONSUMER_CONNECTOR_URL
from pycxids.core.settings import settings

MINIMUM_TOKEN_VALIDITY_SECONDS = 10


class Daps(IdsBase):
    def __init__(self, daps_endpoint: str, private_key_fn: str, client_id: str, debug_messages = False, debug_out_dir: str = '') -> None:
        super().__init__(debug_messages=debug_messages, debug_out_dir=debug_out_dir)
        self.daps_endpoint = daps_endpoint
        #self.private_key_fn = private_key_fn
        self.client_id = client_id
        private_key= ''
        with open(private_key_fn, 'br') as f:
            private_key = f.read()
        self.private_key = private_key
  

    def get_daps_token(self, audience: str = ''):
        now = int(datetime.now().timestamp())
        daps_claim_set = {
            "@context": "https://w3id.org/idsa/contexts/context.jsonld",
            "@type": "ids:DatRequestToken",
            "sub": self.client_id,
            "iss": self.client_id,
            "aud": self.daps_endpoint,
            "iat": now,
            "nbf": now,
            #"exp": now + 36000,
        }
        client_assertion = jwt.encode(daps_claim_set, algorithm='RS256', key=self.private_key)

        params = {
            'grant_type' : 'client_credentials',
            'scope' : "idsc:IDS_CONNECTOR_ATTRIBUTES_ALL",
            'client_assertion_type' : "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            'client_assertion' : client_assertion,
            'resource': audience,
        }

        try:
            r = requests.post(self.daps_endpoint, params=params)
            if not r.ok:
                print(f"Could not fetch token. Reason: {r.reason} Content: {r.content}")
                return None
            j = r.json()
        except Exception as ex:
            print(ex)
            return None

        if self.debug_messages:
            decoded = jwt_decode.decode(j['access_token'])
            decoded_modified = decoded
            decoded_modified['signature'] = decoded['signature'].hex(':')
            self._debug_message(msg = decoded_modified, fn='daps_token.json')
        #exp = decoded['payload']['exp']
        #diff = exp - now
        return j

    @classmethod
    def _daps_token_still_valid(self, token:dict) -> bool:
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



def get_daps_access_token(audience: str = ''):
    daps = get_daps_token(audience=audience)
    return daps['access_token']

daps = Daps(daps_endpoint=DAPS_ENDPOINT, private_key_fn=settings.PRIVATE_KEY_FN, client_id=CLIENT_ID)
def get_daps_token(audience: str = ''):
    """
    deprectated!
    
    audience:   Typically the endpoint for which we request the token.
                If not given, we use the (old) env var
    """
    return daps.get_daps_token(audience=audience)


if __name__ == '__main__':
    daps = Daps(
        daps_endpoint=DAPS_ENDPOINT,
        private_key_fn=settings.PRIVATE_KEY_FN,
        client_id=settings.CLIENT_ID,
        debug_messages=True,
    )
    token = daps.get_daps_token(audience='')
    print(token)