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


def test_service():
    """
    """
    #asset_base_url = 'http://daps-mock:8000/.well-known/jwks.json'
    asset_base_url = 'http://dev:8001/returnparams/'
    # we create a new asset (and friends)
    asset_id = create_asset(base_url=asset_base_url, proxyPath=True)
    policy_id = create_policy(asset_id=asset_id)
    contract_id = create_contract_definition(policy_id=policy_id, asset_id=asset_id)

    sleep(1)
    
    # now, consumer side:

    IDS_PATH = '/api/v1/ids/data'
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

    # tests WITHOUT additinal /suburl
    
    # via consumer data plane
    r = requests.get(f"{consumer_edr['endpoint']}", headers={consumer_edr['authKey']: consumer_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via CONSUMER data plane"

    j = r.json()
    assert 'headers' in j

    # via provider data plane
    r = requests.get(f"{provider_edr['baseUrl']}", headers={provider_edr['authKey']: provider_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via PROVIDER data plane"

    j = r.json()
    assert 'headers' in j
    assert j.get('sub_path') == '', "Path is not empty, but should!"

    # via the data source itself
    # not relevant for now. no difference to the path via provider data plane

    # now test with sum sub-path / suburl
    # via PROVIDER
    suburl = '/suburl/test'
    r = requests.get(f"{provider_edr['baseUrl']}{suburl}", headers={provider_edr['authKey']: provider_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via PROVIDER data plane"

    j = r.json()
    assert 'headers' in j
    assert j.get('sub_path') == suburl, "Suburl not passed through to the backend, but should! Executed via provider data plane."

    # via CONSUMER
    r = requests.get(f"{consumer_edr['endpoint']}{suburl}", headers={consumer_edr['authKey']: consumer_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via CONSUMER data plane"

    j = r.json()
    assert 'headers' in j
    assert j.get('sub_path') == suburl, "Suburl not passed through to the backend, but should! Executed via provider data plane."


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
