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
import pytest
from uuid import uuid4

from pycxids.edc.api import EdcConsumer, EdcProvider
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD, PROVIDER_IDS_ENDPOINT
from pycxids.edc.settings import PROVIDER_IDS_BASE_URL, RECEIVER_SERVICE_BASE_URL

BINARY_FILE = os.environ.get('BINARY_FILE', 'https://heise.cloudimg.io/v7/_www-heise-de_/imgs/18/4/1/5/3/1/5/2/eso2306a-2efe26e8e90f90c1.jpeg')
OUT_FILE = os.environ.get('OUT_FILE', 'out_file.jpg')
OUT_FILE_ORIGIN = os.environ.get('OUT_FILE_ORIGIN', 'out_file_origin.jpg')

def test():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    r1 = requests.get(BINARY_FILE)
    content1 = r1.content
    with open(OUT_FILE_ORIGIN, 'wb') as f:
        f.write(content1)
    file_size_origin = os.stat(OUT_FILE_ORIGIN).st_size
    asset_id, _, _ = provider.create_asset_and_friends(base_url=BINARY_FILE)

    assert asset_id, "Could not create asset"

    sleep(1)

    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url=RECEIVER_SERVICE_BASE_URL,
        )
    agreement_id, transfer_id = consumer.negotiate_and_transfer(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT, asset_id=asset_id)
    provider_edr = consumer.edr_provider_wait(transfer_id=transfer_id)

    provider_data_plane_endpoint = provider_edr.get('baseUrl')

    r = requests.get(provider_data_plane_endpoint, headers={provider_edr['authKey']: provider_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via PROVIDER data plane"

    content = r.content
    
    with open(OUT_FILE, 'wb') as f:
        f.write(content)
    file_size = os.stat(OUT_FILE).st_size

    assert file_size_origin == file_size, "File size of 2 files downloaded directly or via EDC must be identical!"

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
