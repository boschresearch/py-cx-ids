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
def test_create_and_delete():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    # get number of assets before we start - we don't require a clean instance for this test case
    nr_of_assets = provider.get_number_of_elements("/assets")
    nr_of_policies = provider.get_number_of_elements("/policydefinitions")
    nr_of_contractdefinitions = provider.get_number_of_elements("/contractdefinitions")

    # we create a new asset (and friends)
    asset_id = provider.create_asset(base_url='http://daps-mock:8000/.well-known/jwks.json')
    policy_id = provider.create_policy(asset_id=asset_id)
    contract_id = provider.create_contract_definition(policy_id=policy_id, asset_id=asset_id)
    #cd = get_contract_definition(id=contract_id)

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
