# Copyright (c) 2024 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import base64
from copy import deepcopy
import json
from typing import Union
from oauthlib.oauth2 import BackendApplicationClient
import requests
from requests_oauthlib import OAuth2Session
from pycxids.core.jwt_decode import decode_signed, decode

from pycxids.utils.api import GeneralApi

class Sts(GeneralApi):
    """
    Access the STS (Secure Token Service)
    """
    BPN_CREDENTIAL = 'BpnCredential'
    SUMMARY_CREDENTIAL = 'SummaryCredential'
    MEMBERSHIP_CREDENTIAL = 'MembershipCredential'
    TRACEABILITY_CREDENTIAL = 'TraceabilityCredential'
    PCF_CREDENTIAL = 'PcfCredential'

    def __init__(self, base_url: str, client_id: str, client_secret: str, token_url: str, our_did: str) -> None:
        """
        Fetch an access_token for later access to the STS.

        our_did: aka consumer_did
        """
        self.our_did = our_did

        #requests.post(token_url)
        client = BackendApplicationClient(client_id=client_id)
        oauth_session = OAuth2Session(client=client)
        token = oauth_session.fetch_token(token_url=token_url, client_id=client_id, client_secret=client_secret)
        access_token = token.get('access_token', None)
        if not access_token:
            print("Could not fetch access_token.")
        # TODO: This could be improved. e.g. check token has expired, or use the session to fetch data...
        super().__init__(base_url=base_url, headers={'Authorization': f"Bearer {access_token}" })
    
    def get_auth_header(self):
        """
        Only for developing purposes, to e.g. use it with swagger
        """
        return self.headers.get('Authorization')

    def get_sts_token(self, audience: str, bearer_scopes: list, provider_did: str):
        """
        bearer_scopes: This defines what to allow the receiver of the token to lookup in our CredentialService.
        provider_did: The DID of the receiver of this token, who will later use it at our CredentialService endpoint.
        """
        # sts_request_data = {
        #     'token': '',
        #     'audience': audience,
        #     'bearer_access_scope': bearer_scopes,
        #     'client_id': self.client_id,
        #     'client_secret': self.client_secret,
        #     'grant_type': 'client_credentials',
        # }

        # TODO: where does this structure come from?
        # is this standardized anywhere or is this a DIM specific request?
        sts_request_data = {
            "grantAccess": {
                "scope": "read",
                "credentialTypes": bearer_scopes,
                "consumerDid": self.our_did,
                "providerDid": provider_did,
            }
        }
        r = requests.post(f"{self.base_url}", json=sts_request_data, headers=self.headers)
        if not r.ok:
            print(f"{r.status_code} - {r.content}")
            return None
        j = r.json()
        return j.get('jwt')

class CredentialService(GeneralApi):
    """
    For interacting with the CredentialService (CS)
    This is the system that returns credentials (presentations) in return to a given access_token.
    """

    INT_TESTING_DIM = "https://dis-agent-prod.eu10.dim.cloud.sap/api/v1.0.0/iatp"

    def __init__(self, credential_service_base_url: str, access_token: str) -> None:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        super().__init__(base_url=credential_service_base_url, headers=headers)

    def get_vps(self):
        """
        This fetches the VPs from the other organizations' CS with the given access_token.
        """
        data = {
            "@context": [
                "https://w3id.org/tractusx-trust/v0.8",
                "https://identity.foundation/presentation-exchange/submission/v1"
            ],
            "@type": "PresentationQueryMessage",
            "scope": []
        }
        j = self.post(path="/presentations/query", data=data)
        presentations = j.get('presentation')
        return presentations
    
    @classmethod
    def decode_vps(cls, vps: dict, verify_signatures: bool = True):
        """
        The CS returns a list of jwt VPs that contain a list of jwt VCs.
        This is to deocode the content
        """
        if not verify_signatures:
            remove_signatures = True
        vps_decoded = []
        for p in vps:
            decoded_vp = decode(p, remove_signature=remove_signatures)
            vp = deepcopy(decoded_vp)
            
            vp['verifiableCredential'] = []
            vcs = decoded_vp.get('payload', {}).get('vp', {}).get('verifiableCredential')
            # TODO: continue here
            if not isinstance(vcs, list):
                # just to make sure we always have the same situation
                vcs = [vcs]
            for vc in vcs:
                v_d = decode(vc, remove_signature=remove_signatures)
                vp["verifiableCredential"].append(v_d)

            vps_decoded.append(vp)
        return vps_decoded
