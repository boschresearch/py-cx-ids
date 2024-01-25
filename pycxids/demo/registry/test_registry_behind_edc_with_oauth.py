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

from pycxids.registry.api import CxRegistry
from pycxids.models.cxregistry import CxAas, CxSubmodelEndpoint
from pycxids.edc.settings import DUMMY_BACKEND


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

    headers = {
        'Authorization': f"Bearer {token['access_token']}",
        'User-Agent': 'pythonreqquests', # Azure application firewall default rules workaround
    }
    registry = CxRegistry(base_url=REGISTRY_BASE_URL, headers=headers)
    # test the registry with creating an AAS
    cx_ep = f"http://my-provider-control-plane/edc_asset_id/submodel/notuesdforthedemo"
    sm = CxSubmodelEndpoint(endpointAddress=cx_ep, semantic_id='urn:bamm:org:1.0.0:modelname') # TODO: very strict seamntic_id checks!!!
    aas = CxAas(submodels=[sm])
    aas_id = aas.identification
    assert aas_id, "Could not prepare AAS"

    aas_created = registry.create(aas=aas)
    assert aas_created['identification'] == aas_id, "AAS creation did not create with the given AAS id."

    # now create the EDC 'dummy' asset that forwards requests to our registry
    # registry asset needs to be created only ONCE
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

    assert asset_id == registry_asset_id, "Could not create asset."


    # now the consumer side
    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url=RECEIVER_SERVICE_BASE_URL,
    )
    agreement_id = consumer.negotiate_contract_and_wait(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT, asset_id=registry_asset_id)

    # the provider_edr can be directly used - without a consumer data plane
    # in case a consumer data plane call is desired, use the `transfer_and_wait_consumer_edr()`
    provider_edr = consumer.transfer_and_wait_provider_edr(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT,asset_id=registry_asset_id, agreement_id=agreement_id)

    # now, the call against the registry (via the EDC)
    #url = f"{provider_edr['baseUrl']}/lookup/shells"
    url = f"{provider_edr['baseUrl']}/registry/shell-descriptors/{aas_id}"
    headers = {
        provider_edr['authKey']: provider_edr['authCode']
    }
    r = requests.get(url, headers=headers)
    assert r.ok, "Could not lookup shells from registry via EDC"
    j = r.json()
    print(j)

    # since the pure registry part worked, let's now use actual AAS endpoints via EDC
    # first, create the submodel endpoint EDC asset from the AAS we've created earlier
    # Provider side
    sm_asset_id, _, __ = provider.create_asset_and_friends(base_url=DUMMY_BACKEND, proxyPath=True, proxyQueryParams=True)

    # Consumer side
    agreement_id = consumer.negotiate_contract_and_wait(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT, asset_id=sm_asset_id)
    provider_edr = consumer.transfer_and_wait_provider_edr(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT, asset_id=sm_asset_id, agreement_id=agreement_id)
    url = provider_edr['baseUrl']
    headers = {
        provider_edr['authKey']: provider_edr['authCode']
    }
    r = requests.get(url, headers=headers)
    assert r.ok, "Could not submodel data via EDC"
    j = r.json()
    print(j)


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
