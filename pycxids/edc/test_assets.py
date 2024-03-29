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

from pycxids.edc.api import EdcConsumer, EdcProvider
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD, PROVIDER_IDS_ENDPOINT, RECEIVER_SERVICE_BASE_URL
from pycxids.edc.settings import PROVIDER_IDS_BASE_URL, DUMMY_BACKEND
from pycxids.core.settings import settings

TEST_BEFORE_0_5_0_VERSION = os.getenv('TEST_BEFORE_0_5_0_VERSION', '').lower() in ["true"]


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

    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url=RECEIVER_SERVICE_BASE_URL,
        )
    agreement_id, transfer_id = consumer.negotiate_and_transfer(
        provider_ids_endpoint=PROVIDER_IDS_ENDPOINT,
        asset_id=asset_id,
        provider_participant_id=settings.PROVIDER_PARTICIPANT_ID,
        consumer_participant_id=settings.CONSUMER_PARTICIPANT_ID,
    )

    # starting with 0.5.x there is no 2 EDRs any more, just 1 from the provider
    consumer_edr = consumer.edr_consumer_wait(transfer_id=transfer_id)
    consumer_data_plane_endpoint = consumer_edr.get('endpoint')
    r = requests.get(consumer_data_plane_endpoint, headers={consumer_edr['authKey']: consumer_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via CONSUMER data plane"
    j = r.json()
    assert 'headers' in j


    if TEST_BEFORE_0_5_0_VERSION:
        provider_edr = consumer.edr_provider_wait(transfer_id=transfer_id)
        provider_data_plane_endpoint = provider_edr.get('baseUrl')
        r = requests.get(provider_data_plane_endpoint, headers={provider_edr['authKey']: provider_edr['authCode']})
        if not r.ok:
            print(f"{r.status_code} {r.reason} {r.content}")
            assert False, "Could not fetch data via PROVIDER data plane"

        j = r.json()
        assert 'headers' in j

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
