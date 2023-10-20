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
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, PROVIDER_IDS_ENDPOINT, RECEIVER_SERVICE_BASE_URL
from pycxids.edc.settings import DUMMY_BACKEND
from pycxids.core.settings import settings

TEST_BEFORE_0_5_0_VERSION = os.getenv('TEST_BEFORE_0_5_0_VERSION', '').lower() in ["true"]

"""
test_odrl_constraint = {
    "@type": "LogicalConstraint",
    "odrl:and": [
        {
            "@type": "Constraint",
            "odrl:leftOperand": "cx.contract.individual",
            "odrl:operator": {
                "@id": "odrl:eq"
            },
            "odrl:rightOperand": "abc"
        },
        {
            "@type": "Constraint",
            "odrl:leftOperand": "PURPOSE",
            "odrl:operator": {
                "@id": "odrl:eq"
            },
            "odrl:rightOperand": "ID 3.1 Trace"
        },
        {
            "@type": "Constraint",
            "odrl:leftOperand": "FrameworkAgreement.pcf",
            "odrl:operator": {
                "@id": "odrl:eq"
            },
            "odrl:rightOperand": "active"
        }
    ]
}
"""
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


# actual test case
def test_create_and_delete():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    # get number of assets before we start - we don't require a clean instance for this test case
    nr_of_assets = provider.get_number_of_elements("/assets")
    nr_of_policies = provider.get_number_of_elements("/policydefinitions")
    nr_of_contractdefinitions = provider.get_number_of_elements("/contractdefinitions")

    # we create a new asset (and friends)
    # asset_id = provider.create_asset_s3(filename_in_bucket='test', bucket_name='test')
    #asset_id = provider.create_asset(base_url='https://verkehr.autobahn.de/o/autobahn/')
    asset_id = provider.create_asset(base_url=DUMMY_BACKEND)
    policy_id = provider.create_policy(asset_id=asset_id, odrl_constraint=test_odrl_constraint)
    #policy_id = provider.create_policy(asset_id=asset_id)
    contract_id = provider.create_contract_definition(policy_id=policy_id, asset_id=asset_id)
    #cd = get_contract_definition(id=contract_id)

    assert asset_id, "Could not create asset"
    assert policy_id, "Could not create policy"
    assert contract_id, "Could not crate contract definition"

    nr_of_assets_after = provider.get_number_of_elements("/assets")
    assert nr_of_assets_after == nr_of_assets + 1, "Not exactly 1 more asset after creating 1"

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

    edr_init = consumer.edr_start_process(
        provider_ids_endpoint=PROVIDER_IDS_ENDPOINT,
        contract_offer=contract_offer,
        asset_id=asset_id,
        provider_participant_id=settings.PROVIDER_PARTICIPANT_ID,
    )
    #print(json.dumps(edr_init, indent=4))
    negotiation_id = edr_init.get('@id')
    consumer_edr = consumer.edr_for_negotiation(negotiation_id=negotiation_id)
    #print(json.dumps(consumer_edr, indent=4))

    assert consumer_edr, "Could not fetch consumer_edr from receiver service."
    consumer_data_plane_endpoint = consumer_edr.get('edc:endpoint')
    r = requests.get(consumer_data_plane_endpoint, headers={consumer_edr['edc:authKey']: consumer_edr['edc:authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via CONSUMER data plane"
    j = r.json()
    print(json.dumps(j, indent=4))
    assert 'headers' in j or 'roads' in j


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
