# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4
import pytest
from time import sleep
from pycxids.edc.api import EdcConsumer, EdcProvider
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_IDS_ENDPOINT
from pycxids.edc.settings import PROVIDER_EDC_API_KEY, PROVIDER_EDC_BASE_URL, DAPS_JWKS



def test_catalog():
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)
    consumer = EdcConsumer(edc_data_managment_base_url=CONSUMER_EDC_BASE_URL, auth_key=CONSUMER_EDC_API_KEY)

    # just to show, that fetching the catalog works...
    for i in range(0,2):
        asset_id = str(uuid4())
        provider.create_asset_and_friends(base_url=DAPS_JWKS, asset_id=asset_id)
    sleep(2)
    catalog = consumer.get_catalog(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT)
    assert catalog, "Should be possible to fetch"

    # now the actual test case
    # use the same asset_id twice now!
    policy = provider.create_policy(asset_id=None)
    cd = provider.create_contract_definition(policy_id=policy, asset_id=None)

    sleep(2)
    catalog = consumer.get_catalog(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT)
    assert catalog, "Should be possible to fetch"


if __name__ == '__main__':
    pytest.main([__file__, "-s"])