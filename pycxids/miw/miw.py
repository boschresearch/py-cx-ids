# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from typing import Optional, Union
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from pycxids.core.jwt_decode import decode_signed, decode

from pycxids.utils.api import GeneralApi

class Miw(GeneralApi):
    """
    Access the Managed Identity Wallet (MIW) API
    """
    SUMMARY_CREDENTIAL = 'SummaryCredential'
    MEMBERSHIP_CREDENTIAL = 'MembershipCredential'

    def __init__(self, base_url: str, headers = None, client_id: str = None, client_secret: str = None, token_url: str = None) -> None:
        """
        If client_id is given, try to fetch a token with the required other fields.
        If not, you can pass in 'headers' (with an Authorization) that will be used.
        """
        if client_id:
            client = BackendApplicationClient(client_id=client_id)
            oauth_session = OAuth2Session(client=client) # scope not required in MIW API right now
            token = oauth_session.fetch_token(token_url=token_url, client_id=client_id, client_secret=client_secret)
            access_token = token.get('access_token', None)
            if not access_token:
                print("Could not fetch access_token for the portal access.")
            # TODO: This could be improved. e.g. check token has expired, or use the session to fetch data...
            super().__init__(base_url=base_url, headers={'Authorization': f"Bearer {access_token}" })
        else:
            super().__init__(base_url=base_url, headers=headers)
    
    def get_auth_header(self):
        """
        Only for developing purposes, to e.g. use it with swagger
        """
        return self.headers.get('Authorization')

    def get_credentials(self):
        """
        Fetches own credentials
        """
        result = self.get(path="/api/credentials")
        return result

    def create_presentation(self, verifiable_credential: Union[dict, list], aud: str = '', jwt = True):
        """
        A single VC or a list of VCs
        """
        vcs = verifiable_credential
        if not isinstance(verifiable_credential, list):
            vcs = [vcs]
        params = {
            'audience' : aud,
            'asJwt': jwt,
        }
        data = {
            'verifiableCredentials': vcs,
        }
        result = self.post(path="/api/presentations", data=data, params=params)
        return result.get('vp')

    def get_vp(self, credential_type: str = SUMMARY_CREDENTIAL, aud: str = '', jwt = True):
        """
        Search the list of credentials for the given type (use first match)
        and create and return a VP from it.
        Default is 'SummaryCredential'
        """
        credentials = self.get_credentials()
        for cred in credentials.get('content', []):
            cred_type = cred.get('type')
            if isinstance(cred_type, str):
                cred_type = [cred_type] # make sure it is a list
            if credential_type in cred_type:
                vp = self.create_presentation(verifiable_credential=cred, aud=aud)
                return vp['vp']
        return None

    def verify_vp(self, vp, jwt = True):
        params = {
            'asJwt': jwt
        }
        data = {
            'vp': vp
        }
        result = self.post(path="/api/presentations/validation", data=data, params=params)
        return result
