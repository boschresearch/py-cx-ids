# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from uuid import uuid4
import requests
import pytest

from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, PROVIDER_IDS_ENDPOINT, CONSUMER_EDC_BASE_URL, CONSUMER_EDC_API_KEY, RECEIVER_SERVICE_BASE_URL
from pycxids.edc.api import EdcProvider, EdcConsumer

REGISTRY_CLIENT_ID = os.getenv('REGISTRY_CLIENT_ID')
REGISTRY_CLIENT_SECRET = os.getenv('REGISTRY_CLIENT_SECRET')
REGISTRY_TOKEN_ENDPOINT = os.getenv('REGISTRY_TOKEN_ENDPOINT')
REGISTRY_TOKEN_SCOPE = os.getenv('REGISTRY_TOKEN_SCOPE')
REGISTRY_BASE_URL = os.getenv('REGISTRY_BASE_URL')
# we need all of those to continue
assert REGISTRY_CLIENT_ID
assert REGISTRY_CLIENT_SECRET
assert REGISTRY_TOKEN_ENDPOINT
assert REGISTRY_TOKEN_SCOPE
assert REGISTRY_BASE_URL

#REGISTRY_ASSET_ID='registry'

def test():
    # test fetching a token for the registry
    data = {
        'grant_type': 'client_credentials',
        'client_id': REGISTRY_CLIENT_ID,
        'client_secret': REGISTRY_CLIENT_SECRET,
        'scope': REGISTRY_TOKEN_SCOPE,
    }

    r = requests.post(REGISTRY_TOKEN_ENDPOINT, data=data)
    assert r, "Could not fetch auth token for registry access."
    token = r.json()

    # test accessing the registry
    url = f"{REGISTRY_BASE_URL}/lookup/shells"
    headers = {
        'Authorization': f"Bearer {token['access_token']}",
        'User-Agent': 'pythonreqquests',
    }
    r = requests.get(url, headers=headers)
    assert r, "Could not fetch data from registry."
    j = r.json()
    print(j)

    # now create the EDC 'dummy' asset that forwards requests to our registry
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)
    # oauth related asset configs
    oauth_asset_configs = {
        'oauth2:clientId': REGISTRY_CLIENT_ID,
        'oauth2:clientSecret': REGISTRY_CLIENT_SECRET,
        'oauth2:tokenUrl': REGISTRY_TOKEN_ENDPOINT,
        'oauth2:scope': REGISTRY_TOKEN_SCOPE,
    }
    # because it can't be changed after once negotiated, we use a uuid for this
    # easier for demo purposes. In production env, use the 'new' api to
    # update the 'dataAddress' of an Asset (not tested this myself...)
    registry_asset_id = str(uuid4())

    asset_id, _, __ = provider.create_asset_and_friends(
        REGISTRY_BASE_URL,
        asset_id=registry_asset_id,
        proxyBody=True, proxyMethod=True, proxyPath=True, proxyQueryParams=True,
        data_address_additional_props=oauth_asset_configs,
    )

    assert asset_id, "Could not create asset."

    # now the consumer side
    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url=RECEIVER_SERVICE_BASE_URL,
    )
    agreement_id = consumer.negotiate_contract_and_wait_with_asset(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT, asset_id=registry_asset_id)

    # the provider_edr can be directly used - without a consumer data plane
    # in case a consumer data plane call is desired, use the `transfer_and_wait_consumer_edr()`
    provider_edr = consumer.transfer_and_wait_provider_edr(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT,asset_id=registry_asset_id, agreement_id=agreement_id)

    # now, the call against the registry (via the EDC)
    url = f"{provider_edr['baseUrl']}/lookup/shells"
    headers = {
        provider_edr['authKey']: provider_edr['authCode']
    }
    r = requests.get(url, headers=headers)
    assert r.ok, "Could not lookup shells from registry via EDC"
    j = r.json()
    print(j)

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
