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


# actual test case
def test_backend_agreement_id():
    """
    """
    # we create a new asset (and friends)
    asset_id = create_asset(base_url='http://dev:8001/datawithagreementid', proxyQueryParams=True)
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

    provider_ids_endpoint = negotiated_contract.get('coutnerPartyAddress', '')

    # transfer_service needs to be running - as a workaround until we have multiple receiver endpoints
    TRANSFER_SERVICE_ENDPOINT = 'http://dev:8000/transfer'
    r = requests.get(f"{TRANSFER_SERVICE_ENDPOINT}/{asset_id}/{negotiated_contract_id}")

    if not r.ok:
        print(f"{r.reason} - {r.content}")
        assert False
    
    j = r.json()
    print(j)

    daps_access_token = get_daps_access_token(audience='')
    # use the regular (consumer) EDR and add the agreement_id to the query param
    r = requests.get(
            j['consumer_edr']['endpoint'],
            headers={j['consumer_edr']['authKey']: j['consumer_edr']['authCode']},
            params={
                'agreementId': agreement_id,
                'token': daps_access_token,
            },
        )
    if not r.ok:
        print(f"{r.reason} - {r.content}")
        assert False
    
    j = r.json()
    print(j)



if __name__ == '__main__':
    pytest.main([__file__, "-s"])
