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

from pycxids.edc.api import EdcProvider, EdcConsumer
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD
from pycxids.edc.settings import PROVIDER_IDS_BASE_URL, CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_IDS_ENDPOINT


def test():
    """
    Can an existin agreement_id be reused from another EDC instance / identity?
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    backend_endpoint = 'http://dummy-backend:8000/returnparams'
    asset_id, policy_id, contract_id = provider.create_asset_and_friends(base_url=backend_endpoint, proxyPath=True)

    assert asset_id, "Could not create asset"
    assert policy_id, "Could not create policy"
    assert contract_id, "Could not crate contract definition"

    sleep(1)

    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url='http://receiver-service:8000/transfer'
        )
    agreement_id, transfer_id = consumer.negotiate_and_transfer(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT, asset_id=asset_id)
    provider_edr = consumer.edr_provider_wait(transfer_id=transfer_id)

    provider_data_plane_endpoint = provider_edr.get('baseUrl')

    r = requests.get(provider_data_plane_endpoint, headers={provider_edr['authKey']: provider_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via PROVIDER data plane"

    j = r.json()
    assert 'headers' in j

    # now let's try to reuse the agreement_id with another instance in the dataspace
    consumer_third = EdcConsumer(
        edc_data_managment_base_url='http://third-control-plane:9193/api/v1/data',
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url='http://third-receiver-service:8000/transfer'
        )
    transfer_id_third = consumer_third.transfer(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT, asset_id=asset_id, agreement_id=agreement_id)
    provider_edr_third = consumer_third.edr_provider_wait(transfer_id=transfer_id_third)
    assert provider_edr_third
    



if __name__ == '__main__':
    pytest.main([__file__, "-s"])
