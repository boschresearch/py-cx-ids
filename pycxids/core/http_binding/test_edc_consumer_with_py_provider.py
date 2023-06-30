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
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD, PROVIDER_IDS_ENDPOINT
from pycxids.edc.settings import PROVIDER_IDS_BASE_URL


def test():
    """
    """

    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url='http://receiver-service:8000/transfer'
        )

    asset_id = 'demo_asset'
    provider_base_url = 'http://dev:8080'
    agreement_id, transfer_id = consumer.negotiate_and_transfer(provider_ids_endpoint=provider_base_url, asset_id=asset_id)
    #provider_edr = consumer.edr_provider_wait(transfer_id=transfer_id)
    edrs = consumer.edr_tokens(agreement_id=agreement_id)
    print(edrs)

    provider_data_plane_endpoint = provider_edr.get('baseUrl')

    r = requests.get(provider_data_plane_endpoint, headers={provider_edr['authKey']: provider_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via PROVIDER data plane"

    j = r.json()
    assert 'keys' in j

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
