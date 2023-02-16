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

from tests.helper import create_asset, create_policy, create_contract_definition
from pycxids.edc.api import EdcConsumer
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL
from pycxids.core.daps import get_daps_access_token


provider_data_plane_public_endpoint = "http://provider-data-plane:9192/public"
data_source_path = "typenumber1/serialnumber2/submodel"
registry_submodel_data_plane_endpoint_address = f"{provider_data_plane_public_endpoint}/{data_source_path}"
data_source_base_url = "http://dev:8001/returnparams"
asset_base_url = f"{data_source_base_url}"
registry_submodel_aas_endpoint_address = f"{data_source_base_url}/{data_source_path}"

# run with the 2 different options the endpointAddress could be in the registry
@pytest.mark.parametrize("test_input", [registry_submodel_data_plane_endpoint_address, registry_submodel_aas_endpoint_address])
def test_service(test_input):
    """
    This test needs to be executed with 3 different provider control plane settings to get all different possible variations
    
    edc.dataplane.selector.edchttp.properties={ "publicApiUrl": "http://provider-data-plane:9192/public" }
    #edc.dataplane.selector.edchttp.properties={ "publicApiUrl": "http://dev:8001/returnparams" }
    #edc.dataplane.selector.edchttp.properties={ "publicApiUrl": "" }

    The print() commands below show where changes are required or situations could be considered an error.

    backend.py and token_receiver_service need to be running on host 'dev' in the same docker network as the edc-dev-env environment
    Easiest to use Visual Studio Code with 'Dev Containers' and additional config in devcontainer.json
    "runArgs": ["--network", "edc-dev-env_default", "--hostname", "dev" ]
    """
    registry_endpoint_address = test_input

    # we create a new asset (and friends)
    # this would come from the 'subprotocolBody'
    asset_id = create_asset(base_url=asset_base_url, proxyPath=True)
    policy_id = create_policy(asset_id=asset_id)
    contract_id = create_contract_definition(policy_id=policy_id, asset_id=asset_id)

    sleep(1)
    
    # now, consumer side:

    IDS_PATH = '/api/v1/ids/data'
    # this would come from the 'subprotocolBody'
    PROVIDER_IDS_BASE_URL = 'http://provider-control-plane:8282'
    PROVIDER_IDS_ENDPOINT = f"{PROVIDER_IDS_BASE_URL}{IDS_PATH}"

    consumer = EdcConsumer(edc_data_managment_base_url=CONSUMER_EDC_BASE_URL, auth_key=CONSUMER_EDC_API_KEY)
    catalog = consumer.get_catalog(PROVIDER_IDS_ENDPOINT)
    contract_offer = EdcConsumer.find_first_in_catalog(catalog=catalog, asset_id=asset_id)
    negotiated_contract = consumer.negotiate_contract_and_wait(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT, contract_offer=contract_offer)
    negotiated_contract_id = negotiated_contract.get('id', '')
    agreement_id = negotiated_contract.get('contractAgreementId', '')
    print(f"agreementId: {agreement_id}")

    transfer_id = consumer.transfer(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT, asset_id=asset_id, agreement_id=agreement_id)

    r = requests.get(f"http://localhost:8000/transfer/{transfer_id}/token/consumer")
    if not r.ok:
        assert False, "Could not fetch consumer EDR token"
    
    consumer_edr = r.json()

    r = requests.get(f"http://localhost:8000/transfer/{transfer_id}/token/provider")
    if not r.ok:
        assert False, "Could not fetch provider EDR token"
    
    provider_edr = r.json()


    # now test to fetch in different ways
    # via whatever the PROVIDER provides in the registry
    #suburl = registry_endpoint_address.replace(provider_edr['baseUrl'], '') # replace the beginning with empty string

    r = requests.get(registry_endpoint_address, headers={provider_edr['authKey']: provider_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via PROVIDER data plane"

    j = r.json()
    assert 'headers' in j
    assert j.get('sub_path') == data_source_path, "Suburl not passed through to the backend, but should! Executed via provider data plane."
    if data_source_base_url in registry_endpoint_address:
        # the call on the provider side was against the backend directly without the provider data plane
        # that means the backend must have received an EDR token
        assert j.get('headers', {}).get(provider_edr['authKey'].lower() ) == provider_edr['authCode']



    # via CONSUMER
    # and this is the main issue here!
    # how to know what from the registry endpointAddress to replace with the consumer endpoint!
    if registry_endpoint_address == registry_submodel_data_plane_endpoint_address and provider_edr['baseUrl'] == data_source_base_url:
        print("This is not allowed and should never happen! Data plane selector pointing to the backend directly, but registry pointing to the data plane is forbidden and doesn't make sense!")
    else:
        if provider_edr['baseUrl'] == '':
            print("This doesn't work right now and needs a consumer data plane change. Whenever empty, fetch the given URL directly, without a provider data plane.")
        else:
            if provider_edr['baseUrl'] != '' and provider_edr['baseUrl'] not in registry_endpoint_address:
                print("This COULD be considered an error, or the consumer data plane just uses the endpointAddress from the registry.")
            else:                
                consumer_url = registry_endpoint_address.replace(provider_edr['baseUrl'], consumer_edr['endpoint'])
                r = requests.get(consumer_url, headers={consumer_edr['authKey']: consumer_edr['authCode']})
                if not r.ok:
                    print(f"{r.status_code} {r.reason} {r.content}")
                    assert False, "Could not fetch data via CONSUMER data plane"

                j = r.json()
                assert 'headers' in j
                assert j.get('sub_path') == data_source_path, "Suburl not passed through to the backend, but should! Executed via provider data plane."
                if data_source_base_url in registry_endpoint_address:
                    # the call on the provider side was against the backend directly without the provider data plane
                    # that means the backend must have received an EDR token
                    assert j.get('headers', {}).get(provider_edr['authKey'].lower() ) == provider_edr['authCode']


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
