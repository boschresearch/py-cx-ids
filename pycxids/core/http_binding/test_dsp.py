# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from provider import app as provider_app
from consumer import app as consumer_app

from pycxids.core.http_binding.models import CatalogRequestMessage, ContractAgreementMessage, ContractRequestMessage, OdrlOffer, ContractNegotiation, ContractAgreementVerificationMessage

PROVIDER_CALLBACK_BASE_URL = 'http://provider'
CONSUMER_CALLBACK_BASE_URL = 'http://consumer'

provider = TestClient(provider_app, base_url=PROVIDER_CALLBACK_BASE_URL)
consumer = TestClient(consumer_app, base_url=CONSUMER_CALLBACK_BASE_URL)

def requests_post_mock(*args, **kwargs):
    """
    Mocking or better 'mapping' requests.post to the TestClient

    This allows 2 TestClients communicate with each others API via 'requests' calls
    """
    #print(args)
    #print(kwargs)
    url = kwargs.get('url')
    if not url:
        print(f"Mock: request does not contain a url")
        return None
    j = kwargs.get('json')
    if not j:
        print(f"Mock: request post does not contain data")
        return None
    if url.startswith(CONSUMER_CALLBACK_BASE_URL):
        r = consumer.post(url=url, json=j)
    if url.startswith(PROVIDER_CALLBACK_BASE_URL):
        r = provider.post(url=url, json=j)
    return r


@patch('requests.post', Mock(side_effect=requests_post_mock))
def test_negotiation():
    # catalog
    catalog_request_message = CatalogRequestMessage()
    data = catalog_request_message.dict(exclude_unset=False)
    r = provider.post('/catalog/request', json=data)
    catalog = r.json()
    #print(catalog)
    dataset = catalog.get('dcat:dataset', [None])[0]
    assert dataset, "No dataset in catalog!"

    # negotiation
    # start -> requested
    dataset_id = dataset.get('@id')
    has_policy_field = dataset.get('odrl:hasPolicy', [None])[0]
    assert has_policy_field, "Dataset from catalog needs a policy associated with!"
    offer = OdrlOffer.parse_obj(has_policy_field)
    offer.odrl_target = dataset_id
    contract_request_id = str(uuid4())
    contract_request_message = ContractRequestMessage(
        field_id=contract_request_id,
        dspace_dataset=dataset_id,
        dspace_offer=offer,
        dscpace_callback_address=CONSUMER_CALLBACK_BASE_URL,
    )
    data = contract_request_message.dict(exclude_unset=False)

    # the next step uses an internal 'requests' call that is mocked with the @patch test case annotation
    r = provider.post('/negotiations/request', json=data)
    assert r.status_code == 200
    j = r.json()
    contract_negotiation = ContractNegotiation.parse_obj(j)
    # requested -> agreed
    r = consumer.get(f'/negotiations/{contract_request_id}/agreement') # TODO: location header?
    assert r.status_code == 200
    contract_agreement_message_received = ContractAgreementMessage.parse_obj(r.json())

    # agreed -> verified



if __name__ == '__main__':
    pytest.main([__file__, "-s"])

