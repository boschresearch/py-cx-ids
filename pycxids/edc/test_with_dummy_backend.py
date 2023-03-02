# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


import os
import sys
from time import sleep
import json
import requests
from requests.auth import HTTPBasicAuth
import pytest
from uuid import uuid4

from pycxids.edc.api import EdcProvider
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD
from pycxids.edc.settings import PROVIDER_IDS_BASE_URL

# actual test case
def test():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    backend_endpoint = 'http://dummy-backend:8000/returnparams'
    asset_id, policy_id, contract_id = provider.create_asset_and_friends(base_url=backend_endpoint, proxyPath=True)

    assert asset_id, "Could not create asset"
    assert policy_id, "Could not create policy"
    assert contract_id, "Could not crate contract definition"

    sleep(1)
    
    auth = HTTPBasicAuth(username=API_WRAPPER_USER, password=API_WRAPPER_PASSWORD)
    params = {
        "provider-connector-url": PROVIDER_IDS_BASE_URL,
    }
    url = f"{API_WRAPPER_BASE_URL}/{asset_id}/xxx"

    r = requests.get(url, auth=auth, params=params)

    if not r.ok:
        print(f"{r.reason} {r.content}")
        assert False, "Could not fetch data"
    
    print(r.content)

    j = r.json()
    assert 'keys' in j

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
