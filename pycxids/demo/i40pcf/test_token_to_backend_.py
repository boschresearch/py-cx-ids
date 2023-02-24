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
from pycxids.edc.api import EdcProvider
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD

DAPS_TOKEN_SERVICE_ENDPOINT = os.getenv('DAPS_TOKEN_SERVICE_ENDPOINT', "http://localhost:8004/token")
BASIC_AUTH_USERNAME = os.getenv('BASIC_AUTH_USERNAME', 'admin')
BASIC_AUTH_PASSWORD = os.getenv('BASIC_AUTH_PASSWORD', 'admin')


def test_token():

    edc = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    asset_id, policy_id, cd_id = edc.create_asset_and_friends(base_url="http://dev:8001/returnparams", proxyPath=True, proxyQueryParams=True)
    sleep(1)

    # second part, try to fetch them via the consumer EDC
    sleep(1)
    auth = HTTPBasicAuth(username=API_WRAPPER_USER, password=API_WRAPPER_PASSWORD)
    params = {
        "provider-connector-url": "http://provider-control-plane:8282",
    }


    # get a fresh DAPS token
    r = requests.get(DAPS_TOKEN_SERVICE_ENDPOINT, auth=HTTPBasicAuth(username=BASIC_AUTH_USERNAME, password=BASIC_AUTH_PASSWORD))
    if not r.ok:
        assert False, "Could not fetch DAPS token"
    j = r.json()
    token = j['access_token']

    # fetch data and pass a 'token' query param        
    url = f"{API_WRAPPER_BASE_URL}/{asset_id}/xxx"
    params['token'] = token
    r = requests.get(url, auth=auth, params=params)

    if not r.ok:
        print(f"{r.reason} {r.content}")
        assert False, "Could not fetch data"

    j = r.json()
    print(j)
    assert j.get('query_params', {}).get('token') == token, "Token not transferred to the bakcend service."

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
