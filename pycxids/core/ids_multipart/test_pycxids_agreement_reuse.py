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
from pycxids.core.ids_multipart.ids_multipart import IdsMultipartConsumer
from pycxids.core.settings import settings

from pycxids.edc.api import EdcProvider
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD, PROVIDER_EDC_VALIDATION_ENDPOINT
from pycxids.edc.settings import PROVIDER_IDS_BASE_URL, CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_IDS_ENDPOINT


def test():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    backend_endpoint = 'http://dummy-backend:8000/returnparams'
    asset_id, policy_id, contract_id = provider.create_asset_and_friends(base_url=backend_endpoint, proxyPath=True)

    assert asset_id, "Could not create asset"
    assert policy_id, "Could not create policy"
    assert contract_id, "Could not crate contract definition"

    sleep(1)
    # Consumer
    ids = IdsMultipartConsumer(
        private_key_fn='./edc-dev-env/vault_secrets/consumer.key',
        provider_connector_ids_endpoint='http://provider-control-plane:8282/api/v1/ids/data',
        consumer_connector_urn='urn:uuid:consumer',
        consumer_connector_webhook_url='http://consumer-webhook-service:8000/webhook',
        consumer_webhook_message_base_url='http://consumer-webhook-service:8000/messages',
        consumer_webhook_message_username='someuser',
        consumer_webhook_message_password='somepassword',
    )
    offers = ids.get_offers(asset_id=asset_id)
    offer = offers[0]
    agreement_id = ids.negotiate(contract_offer=offer)
    edr_provider = ids.transfer(asset_id=asset_id, agreement_id=agreement_id)
    print(edr_provider)

    # Third
    ids = IdsMultipartConsumer(
        private_key_fn='./edc-dev-env/vault_secrets/third.key',
        provider_connector_ids_endpoint='http://provider-control-plane:8282/api/v1/ids/data',
        consumer_connector_urn='urn:uuid:third',
        consumer_connector_webhook_url='http://third-webhook-service:8000/webhook',
        consumer_webhook_message_base_url='http://third-webhook-service:8000/messages',
        consumer_webhook_message_username='someuser',
        consumer_webhook_message_password='somepassword',
    )
    """
    offers = ids.get_offers(asset_id=asset_id)
    offer = offers[0]
    agreement_id = ids.negotiate(contract_offer=offer)
    """
    edr_provider_third = ids.transfer(asset_id=asset_id, agreement_id=agreement_id)
    print(edr_provider_third)
    url = edr_provider_third.get('endpoint')
    auth_key = edr_provider_third.get('authKey')
    auth_code = edr_provider_third.get('authCode')
    r = requests.get(url, headers={
        auth_key: auth_code
    })
    if not r.ok:
        print(f"{r.status_code} - {r.reason} - {r.content}")
        assert False
    j = r.json()
    print(j)
    assert 'headers' in j

    edc_contract_agreement_id = j.get('headers', {}).get('edc-contract-agreement-id', None)
    if edc_contract_agreement_id:
        # only possible in 0.3.0. first version in which the agreement ID is sent to the backend in the http header
        non_urn_agreement_id = agreement_id.replace('urn:contractagreement:', '')
        assert edc_contract_agreement_id != non_urn_agreement_id, "It should not be possible to fetch data under someone elses agreement_id!"


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
