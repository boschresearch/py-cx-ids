# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from time import sleep
import pytest
import requests
from requests.auth import HTTPBasicAuth
from pycxids.demo.i40pcf.init import get_endpoint_hashes
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD
from pycxids.utils.helper import print_red

DAPS_TOKEN_SERVICE_ENDPOINT = os.getenv('DAPS_TOKEN_SERVICE_ENDPOINT', "http://daps-token-service:8000/token")
BASIC_AUTH_USERNAME = os.getenv('BASIC_AUTH_USERNAME', 'admin')
BASIC_AUTH_PASSWORD = os.getenv('BASIC_AUTH_PASSWORD', 'dontuseinpublic')

REGISTRY_ENDPOINT= os.getenv('REGISTRY_ENDPOINT', 'https://registry.dpp40-2-v2.industrialdigitaltwin.org/')


def test_fetch_i40_pcf():
    """
    Fetches every endpoint via a its individual EDC asset_id
    """
    api_wrapper_auth = HTTPBasicAuth(username=API_WRAPPER_USER, password=API_WRAPPER_PASSWORD)
    params = {
        "provider-connector-url": "http://provider-control-plane:8282",
        "Email": "@phoenixcontact",
    }

    hashed_endpoints = get_endpoint_hashes(registry_base_url=REGISTRY_ENDPOINT)
    good = []
    bad = []
    counter = 0
    for asset_id in hashed_endpoints:

        """
        # get a fresh DAPS token
        r = requests.get(DAPS_TOKEN_SERVICE_ENDPOINT, auth=HTTPBasicAuth(username=BASIC_AUTH_USERNAME, password=BASIC_AUTH_PASSWORD))
        if not r.ok:
            assert False, "Could not fetch DAPS token"
        token_data = r.json()
        #optionally pass a 'daps' token query param
        params['daps'] = token_data['access_token']
        """

        # fetch data
        url = f"{API_WRAPPER_BASE_URL}/{asset_id}/xxx"
        
        r = requests.get(url, auth=api_wrapper_auth, params=params)

        if not r.ok:
            print(f"{r.reason} {r.content}")
            bad.append(asset_id)
            continue
        good.append(asset_id)
        print(r.content)
        print("")
        counter = counter + 1
        print_red(f"{counter}/{len(hashed_endpoints)}")

    assert len(hashed_endpoints) == len(good), "Not all created assets could be fetched."

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
