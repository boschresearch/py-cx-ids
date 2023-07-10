# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from pycxids.utils.api import GeneralApi

class Miw(GeneralApi):
    """
    Access the Managed Identity Wallet (MIW) API
    """
    def __init__(self, base_url: str, headers = None, client_id: str = None, client_secret: str = None, token_url: str = None, scope:str = None) -> None:
        """
        If client_id is given, try to fetch a token with the required other fields.
        If not, you can pass in 'headers' (with an Authorization) that will be used.
        """
        if client_id:
            client = BackendApplicationClient(client_id=client_id)
            oauth_session = OAuth2Session(client=client, scope=scope)
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


if __name__ == '__main__':
    secret_fn = './edc-dev-env/vault_secrets/provider.miw.secret'
    secret = None
    with open(secret_fn, 'rt') as f:
        secret = f.read()
    assert secret
    # TODO: get from settings

    tx_ssi_miw_url="https://managed-identity-wallets-new.int.demo.catena-x.net"
    tx_ssi_oauth_token_url="https://centralidp.int.demo.catena-x.net/auth/realms/CX-Central/protocol/openid-connect/token"
    tx_ssi_oauth_client_id="sa209"
    tx_ssi_endpoint_audience="http://consumer-control-plane:8282/api/v1/dsp"
    miw = Miw(base_url=tx_ssi_miw_url, client_id=tx_ssi_oauth_client_id, client_secret=secret, token_url=tx_ssi_oauth_token_url)
    bearer_token = miw.get_auth_header()
    print(bearer_token)
    credentials = miw.get_credentials()
    credentials_str = json.dumps(credentials, indent=4)
    print(credentials_str)
    with open('miw_token.json', 'wt') as f:
        f.write(credentials_str)

