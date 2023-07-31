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
from pycxids.core.auth.auth_factory import MiwAuthFactory
from pycxids.core.http_binding.models_local import TransferStateStore
from pycxids.core.http_binding.settings import CONSUMER_CALLBACK_BASE_URL
from pycxids.core.settings import DAPS_ENDPOINT

from pycxids.edc.api import EdcConsumer, EdcProvider
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, DUMMY_BACKEND, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD, PROVIDER_EDC_BASE_URL, PROVIDER_IDS_ENDPOINT, RECEIVER_SERVICE_BASE_URL
from pycxids.edc.settings import PROVIDER_IDS_BASE_URL
from pycxids.core.settings import settings
from pycxids.core.http_binding.dsp_client_consumer_api import *


def test():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    # get number of assets before we start - we don't require a clean instance for this test case
    nr_of_assets = provider.get_number_of_elements("/assets")
    nr_of_policies = provider.get_number_of_elements("/policydefinitions")
    nr_of_contractdefinitions = provider.get_number_of_elements("/contractdefinitions")

    # we create a new asset (and friends)
    asset_id = provider.create_asset(base_url=DUMMY_BACKEND)
    policy_id = provider.create_policy(asset_id=asset_id)
    contract_id = provider.create_contract_definition(policy_id=policy_id, asset_id=asset_id)
    #cd = get_contract_definition(id=contract_id)

    assert asset_id, "Could not create asset"
    assert policy_id, "Could not create policy"
    assert contract_id, "Could not crate contract definition"

    nr_of_assets_after = provider.get_number_of_elements("/assets")
    assert nr_of_assets_after == nr_of_assets + 1, "Not exactly 1 more asset after creating 1"

    sleep(1)

    # now consume via the pycxids implementation
    consumer_callback_base_url = CONSUMER_CALLBACK_BASE_URL
    auth_factory = MiwAuthFactory(
        miw_base_url='http://miw-server:8080/miw',
        client_id='consumer',
        client_secret='000',
        token_url='http://miw-server:8080/miw/token'
    )
    consumer = DspClientConsumerApi(provider_base_url=PROVIDER_IDS_ENDPOINT, auth=auth_factory)
    #catalog = consumer.fetch_catalog()
    # we already know which asset_id
    offers = consumer.get_offers_for_asset(asset_id=asset_id)
    negotiation = consumer.negotiation(dataset_id=asset_id, offer=offers[0], consumer_callback_base_url=consumer_callback_base_url, provider_base_url=PROVIDER_IDS_ENDPOINT)

    negotiation_process_id = negotiation.get('dspace:processId')
    if not negotiation_process_id:
        negotiation_process_id = negotiation.get('https://w3id.org/dspace/v0.8/processId')
    # and now get the message from the receiver api (proprietary api)
    agreement = consumer.negotiation_callback_result(id=negotiation_process_id, consumer_callback_base_url=consumer_callback_base_url)
    print(agreement)
    agreement_id = agreement.get('dspace:agreement', {}).get('@id')
    assert agreement_id, "Did not get an agreementId"
    transfer = consumer.transfer(agreement_id_received=agreement_id, consumer_callback_base_url=consumer_callback_base_url, provider_base_url=PROVIDER_IDS_ENDPOINT)
    print(transfer)
    transfer_id = transfer.get('@id')
    transfer_process_id = transfer.get('dspace:processId')
    if not transfer_process_id:
        # TODO: it seem EDC uses old correlationId here
        transfer_process_id = transfer.get('https://w3id.org/dspace/v0.8/correlationId')
    if not transfer_process_id:
        transfer_process_id = transfer.get('dspace:correlationId')
    transfer_message = consumer.transfer_callback_result(id=transfer_process_id, consumer_callback_base_url=consumer_callback_base_url)
    print(transfer_message)
    transfer_state_received = TransferStateStore.parse_obj(transfer_message)
    print(transfer_state_received)
    auth_code = transfer_state_received.data_address.edc_auth_code
    auth_key = transfer_state_received.data_address.edc_auth_key
    endpoint = transfer_state_received.data_address.edc_endpoint

    # actual request of the data
    headers = {
        auth_key: auth_code
    }
    r = requests.get(endpoint, headers=headers)
    j = r.json()
    assert 'headers' in j


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
