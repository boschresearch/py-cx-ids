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
from pycxids.demo.i40pcf.init import create_edc_assets_from_registry_submodesl
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD


DAPS_TOKEN_SERVICE_ENDPOINT = os.getenv('DAPS_TOKEN_SERVICE_ENDPOINT', "http://localhost:8004/token")
BASIC_AUTH_USERNAME = os.getenv('BASIC_AUTH_USERNAME', 'admin')
BASIC_AUTH_PASSWORD = os.getenv('BASIC_AUTH_PASSWORD', 'admin')


def test_create_and_fetch_i40_pcf():
    # create the pcf assets
    asset_ids = create_edc_assets_from_registry_submodesl(
        registry_base_url='https://registry.dpp40-2-v2.industrialdigitaltwin.org/',
        edc_data_managment_base_url=PROVIDER_EDC_BASE_URL,
        edc_auth_key=PROVIDER_EDC_API_KEY
    )

    # second part, try to fetch them via the consumer EDC
    sleep(1)
    auth = HTTPBasicAuth(username=API_WRAPPER_USER, password=API_WRAPPER_PASSWORD)
    params = {
        "provider-connector-url": "http://provider-control-plane:8282",
        "Email": "@phoenixcontact",
    }

    good = []
    bad = []
    for asset_id in asset_ids:

        # get a fresh DAPS token
        r = requests.get(DAPS_TOKEN_SERVICE_ENDPOINT, auth=HTTPBasicAuth(username=BASIC_AUTH_USERNAME, password=BASIC_AUTH_PASSWORD))
        if not r.ok:
            assert False, "Could not fetch DAPS token"
        token_data = r.json()

        # fetch data and pass a 'token' query param
        url = f"{API_WRAPPER_BASE_URL}/{asset_id}/xxx"
        params['daps'] = token_data['access_token']
        r = requests.get(url, auth=auth, params=params)

        if not r.ok:
            print(f"{r.reason} {r.content}")
            bad.append(asset_id)
            continue
        good.append(asset_id)
        print(r.content)

    assert len(asset_ids) == len(good), "Not all created assets could be fetched."

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
