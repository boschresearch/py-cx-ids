# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from pycxids.utils.api import GeneralApi

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

class Portal(GeneralApi):
    def __init__(self, portal_base_url: str, client_id: str, client_secret: str, token_url: str) -> None:
        client = BackendApplicationClient(client_id=client_id)
        oauth_session = OAuth2Session(client=client)
        token = oauth_session.fetch_token(token_url=token_url, client_id=client_id, client_secret=client_secret)
        access_token = token.get('access_token', None)
        if not access_token:
            print("Could not fetch access_token for the portal access.")
        # TODO: This could be improved. e.g. check token has expired, or use the session to fetch data...
        super().__init__(base_url=portal_base_url, headers={'Authorization': f"Bearer {access_token}" })

    def discover_edc_endpoint(self, bpn: str):
        """
        Possible to request exactly for 1 BPN
        """
        data = [
            bpn
        ]
        result = self.post('/api/administration/connectors/discovery', data=data)
        endpoints = []
        for x in result:
            if x.get('bpn') == bpn:
                return x.get('connectorEndpoint')

        return [] # nothing found for the given BPN
