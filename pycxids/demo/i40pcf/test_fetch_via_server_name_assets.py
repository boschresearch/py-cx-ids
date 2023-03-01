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
from pycxids.demo.i40pcf.init import get_endpoints, get_servername, hashed_asset_id
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD
from pycxids.utils.helper import print_red


DAPS_TOKEN_SERVICE_ENDPOINT = os.getenv('DAPS_TOKEN_SERVICE_ENDPOINT', "http://daps-token-service:8000/token")
BASIC_AUTH_USERNAME = os.getenv('BASIC_AUTH_USERNAME', 'admin')
BASIC_AUTH_PASSWORD = os.getenv('BASIC_AUTH_PASSWORD', 'dontuseinpublic')

REGISTRY_ENDPOINT= os.getenv('REGISTRY_ENDPOINT', 'https://registry.dpp40-2-v2.industrialdigitaltwin.org/')


def test_fetch_i40_pcf():
    """
    Fetch all endpoints via EDC assets created for each individual server name (not the entire endpoint address)!
    This makes the process muc faster, because existing agreements can be reused.
    
    If using the api-wrapper, make sure it is configured with: wrapper.cache.agreement.enabled=true
    """
    api_wrapper_auth = HTTPBasicAuth(username=API_WRAPPER_USER, password=API_WRAPPER_PASSWORD)
    params = {
        "provider-connector-url": "http://provider-control-plane:8282",
        "Email": "@phoenixcontact",
    }


    endpoints = get_endpoints(registry_base_url=REGISTRY_ENDPOINT)

    good = []
    bad = []
    counter = 0
    for endpoint in endpoints:

        server = get_servername(url=endpoint)
        path = endpoint.replace(server, '')
        asset_id = hashed_asset_id(value=server)

        # fetch data and pass a 'token' query param
        url = f"{API_WRAPPER_BASE_URL}/{asset_id}{path}"
        r = requests.get(url, auth=api_wrapper_auth, params=params)

        if not r.ok:
            print(f"{r.reason} {r.content}")
            bad.append(asset_id)
            continue
        good.append(asset_id)
        print(r.content)
        print("")
        counter = counter + 1
        print_red(f"{counter}/{len(endpoints)}")

    assert len(endpoints) == len(good), "Not all created assets could be fetched."

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
