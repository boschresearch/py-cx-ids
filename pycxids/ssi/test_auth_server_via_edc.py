# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


import os
from time import sleep
import json
import requests
import pytest
from uuid import uuid4

from pycxids.edc.api import EdcConsumer, EdcProvider
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, PROVIDER_IDS_ENDPOINT, RECEIVER_SERVICE_BASE_URL
from pycxids.edc.settings import DUMMY_BACKEND
from pycxids.core.settings import settings

test_odrl_constraint = {
    "@type": "LogicalConstraint",
    "odrl:and": [
        {
            "@type": "Constraint",
            "odrl:leftOperand": "FrameworkAgreement.membership",
            "odrl:operator": {
                "@id": "odrl:eq"
            },
            "odrl:rightOperand": "active"
        }
    ]
}


def test_():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    #asset_id = provider.create_asset(base_url='', data_address_type='HttpAccessToken')
    # for now we need HttpData because only this recieves agreement and BPN inside the EDR token
    # also a base_url is required with HttpData
    asset_id = provider.create_asset(base_url='http://localhost', data_address_type='HttpData')
    policy_id = provider.create_policy(asset_id=asset_id, odrl_constraint=test_odrl_constraint)
    contract_id = provider.create_contract_definition(policy_id=policy_id, asset_id=asset_id)

    assert asset_id, "Could not create asset"
    assert policy_id, "Could not create policy"
    assert contract_id, "Could not crate contract definition"

    sleep(1)

    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url=RECEIVER_SERVICE_BASE_URL,
        )
    catalog = consumer.get_catalog(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT)
    contract_offer = consumer.find_first_in_catalog(catalog=catalog, asset_id=asset_id)
    assert contract_offer, "Could not find matching offer in catalog"
    #print(json.dumps(contract_offer, indent=4))
    # TODO: check policy content

    agreement_data = consumer.negotiate_contract_and_wait(
        provider_ids_endpoint=PROVIDER_IDS_ENDPOINT,
        contract_offer=contract_offer,
        asset_id=asset_id,
        provider_participant_id=settings.PROVIDER_PARTICIPANT_ID,
    )
    agreement_id = agreement_data.get('edc:contractAgreementId')
    transfer_id = consumer.transfer(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT,
                                    asset_id=asset_id,
                                    agreement_id=agreement_id,
                                    provider_participant_id=settings.PROVIDER_PARTICIPANT_ID)
    consumer_edr = consumer.edr_consumer_wait(transfer_id=transfer_id)

    assert consumer_edr, "Could not fetch consumer_edr from receiver service."
    
    form_data = {
        'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        'client_assertion': 'hello=world',
    }
    consumer_data_plane_endpoint = consumer_edr.get('edc:endpoint') or consumer_edr.get('endpoint')
    auth_key = consumer_edr.get('edc:authKey') or consumer_edr.get('authKey')
    auth_code = consumer_edr.get('edc:authCode') or consumer_edr.get('authCode')
    r = requests.post(consumer_data_plane_endpoint,
                      headers={auth_key : auth_code },
                      data=form_data)
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via CONSUMER data plane"
    j = r.json()
    print(json.dumps(j, indent=4))
    assert 'access_token' in j

    headers = {'Authorization': f"Bearer {j.get('access_token')}"}
    r = requests.get('http://dev:5001/protected', headers=headers)
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch protected data with token"
    data = r.json()
    print(json.dumps(data, indent=4))


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
