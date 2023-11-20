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
from pycxids.core.http_binding.crypto_utils import private_key_from_seed_file
from pycxids.core.http_binding.dsp_client_consumer_api import DspClientConsumerApi

from pycxids.edc.api import EdcConsumer, EdcProvider
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, PROVIDER_IDS_ENDPOINT, RECEIVER_SERVICE_BASE_URL
from pycxids.edc.settings import DUMMY_BACKEND
from pycxids.edc.settings import PROVIDER_IDS_ENDPOINT
from pycxids.miw.god_mode_auth_factory import GodModeAuth
from pycxids.core.settings import settings

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from pycxids.miw.god_mode_helper import god_mode_fetch

SEED_INSECURE_FN = os.getenv('SEED_INSECURE_FN', './edc-dev-env/vault_secrets/seed.insecure')
private_key = private_key_from_seed_file(SEED_INSECURE_FN)


#BPN_VIP = "BPNL00000003B5MJ"
BPN_VIP = "BPNL000000000VIP"

#BASE_URL = DUMMY_BACKEND
BASE_URL = 'https://verkehr.autobahn.de/o/autobahn/'
CONSUMER_CALLBACK_BASE_URL = os.getenv('CONSUMER_CALLBACK_BASE_URL', None)
assert CONSUMER_CALLBACK_BASE_URL, "Please set CONSUMER_CALLBACK_BASE_URL"

# actual test case
def test():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    # get number of assets before we start - we don't require a clean instance for this test case
    nr_of_assets = provider.get_number_of_elements("/assets")
    nr_of_policies = provider.get_number_of_elements("/policydefinitions")
    nr_of_contractdefinitions = provider.get_number_of_elements("/contractdefinitions")

    asset_id = provider.create_asset(base_url=BASE_URL)
    policy_id = provider.create_policy(asset_id=asset_id)

    access_policy_vip = provider.create_access_policy(bpn=BPN_VIP)

    contract_id_vip = provider.create_contract_definition(policy_id=policy_id, asset_id=asset_id, access_policy_id=access_policy_vip)

    assert asset_id, "Could not create asset"
    assert policy_id, "Could not create policy"
    assert contract_id_vip, "Could not crate contract definition for VIP"

    sleep(1)

    # regular EDC catalog request
    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url=RECEIVER_SERVICE_BASE_URL,
        )
    catalog = consumer.get_catalog(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT)
    catalog_str = json.dumps(catalog, indent=4)
    with open('catalog.json', 'wt') as f:
        f.write(catalog_str)
    dataset_match = []
    for dataset in catalog['dcat:dataset']:
        id = dataset.get('@id')
        if id == asset_id:
            dataset_match.append(dataset)

    assert len(dataset_match) == 0, "Shouldn't be able to see the restricted asset at all."

    data = god_mode_fetch(asset_id=asset_id, bpn=BPN_VIP, provider_ids_endpoint=PROVIDER_IDS_ENDPOINT)
    assert data
    print(data)


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
