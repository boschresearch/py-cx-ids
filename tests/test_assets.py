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

from helper import *


# actual test case
def test_create_and_delete():
    """
    """
    # get number of assets before we start - we don't require a clean instance for this test case
    nr_of_assets = get_number_of_elements(f"{PROVIDER_EDC_BASE_URL}/assets")
    nr_of_policies = get_number_of_elements(f"{PROVIDER_EDC_BASE_URL}/policydefinitions")
    nr_of_contractdefinitions = get_number_of_elements(f"{PROVIDER_EDC_BASE_URL}/contractdefinitions")

    # we create a new asset (and friends)
    asset_id = create_asset(base_url='http://daps-mock:8000/.well-known/jwks.json')
    policy_id = create_policy(asset_id=asset_id)
    contract_id = create_contract_definition(policy_id=policy_id, asset_id=asset_id)
    cd = get_contract_definition(id=contract_id)

    sleep(1)
    
    auth = HTTPBasicAuth(username=API_WRAPPER_USER, password=API_WRAPPER_PASSWORD)
    params = {
        "provider-connector-url": "http://provider-control-plane:8282",
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
