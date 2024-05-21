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
from datetime import datetime

from pycxids.edc.api import EdcConsumer, EdcProvider
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, PROVIDER_IDS_ENDPOINT, RECEIVER_SERVICE_BASE_URL
from pycxids.edc.settings import DUMMY_BACKEND
from pycxids.core.settings import settings


test_odrl_constraint = {
    "@type": "LogicalConstraint",
    "odrl:and": [
        {
            "@type": "Constraint",
            "odrl:leftOperand": "UsagePurpose",
            "odrl:operator": {
                "@id": "odrl:eq"
            },
            "odrl:rightOperand": "cx.core.industrycore:1"
        },
        {
            "@type": "Constraint",
            "odrl:leftOperand": "https://w3id.org/catenax/policy/UsagePurpose",
            "odrl:operator": {
                "@id": "odrl:eq"
            },
            "odrl:rightOperand": "cx.core.industrycore:1"
        },
        {
            "@type": "Constraint",
            "odrl:leftOperand": "cx-policy:UsagePurpose",
            "odrl:operator": {
                "@id": "odrl:eq"
            },
            "odrl:rightOperand": "cx.core.industrycore:1"
        },
        {
            "@type": "Constraint",
            "odrl:leftOperand": {
                "@id": "https://w3id.org/catenax/policy/UsagePurpose"
            },
            "odrl:operator": {
                "@id": "odrl:eq"
            },
            "odrl:rightOperand": "cx.core.industrycore:1"
        },

    ]
}


# actual test case
def test():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    # get number of assets before we start - we don't require a clean instance for this test case
    nr_of_assets = provider.get_number_of_elements("/v3/assets")

    # we create a new asset (and friends)
    # asset_id = provider.create_asset_s3(filename_in_bucket='test', bucket_name='test')
    asset_id = provider.create_asset(base_url='https://verkehr.autobahn.de/o/autobahn/')
    #asset_id = provider.create_asset(base_url=DUMMY_BACKEND)
    policy_id = provider.create_policy(asset_id=asset_id, odrl_constraint=test_odrl_constraint)
    contract_id = provider.create_contract_definition(policy_id=policy_id, asset_id=asset_id)

    assert asset_id, "Could not create asset"
    assert policy_id, "Could not create policy"
    assert contract_id, "Could not crate contract definition"

    nr_of_assets_after = provider.get_number_of_elements("/v3/assets")
    assert nr_of_assets_after == nr_of_assets + 1, "Not exactly 1 more asset after creating 1"

    sleep(1)

    start = datetime.now()
    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url=RECEIVER_SERVICE_BASE_URL,
        )

    # PROVIDER_PARTICIPANT_ID can no longer be exctracted from the catalog, since it is already
    # required for authentication with the IATP
    catalog = consumer.get_catalog(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT, provider_participant_id=settings.PROVIDER_PARTICIPANT_ID)
    catalog_context = catalog.get('@context')
    with open('catalog_context.json', 'wt') as f:
        f.write(json.dumps(catalog_context, indent=True))
    contract_offer = consumer.find_first_in_catalog(catalog=catalog, asset_id=asset_id)
    assert contract_offer, "Could not find matching offer in catalog"
    with open('catalog_offer.json', 'wt') as f:
        f.write(json.dumps(contract_offer, indent=True))

    provider_edc_participant_id = settings.PROVIDER_PARTICIPANT_ID
    assert provider_edc_participant_id, "Could not find edc:participantId from received catalog result"

    negotiated_contract = consumer.negotiate_contract_and_wait(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT,
        contract_offer=contract_offer, asset_id=asset_id,
        provider_participant_id=provider_edc_participant_id,
        consumer_participant_id=settings.CONSUMER_PARTICIPANT_ID,
        timeout=60
        )
    assert negotiated_contract, "Could not negotiate contract"
    agreement_id = negotiated_contract.get('contractAgreementId', '') or negotiated_contract.get('edc:contractAgreementId', '')
    print(f"agreementId: {agreement_id}")

    transfer_id = consumer.transfer(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT,
        asset_id=asset_id, agreement_id=agreement_id, provider_participant_id=settings.PROVIDER_PARTICIPANT_ID,
        )

    consumer_edr = consumer.edr_consumer_wait(transfer_id=transfer_id)

    assert consumer_edr, "Could not fetch consumer_edr from receiver service."
    consumer_data_plane_endpoint = consumer_edr.get('https://w3id.org/edc/v0.0.1/ns/endpoint')
    authorization = consumer_edr.get('https://w3id.org/edc/v0.0.1/ns/authorization')
    headers = {
        "Authorization": authorization # shouldn't this use 'Bearer' ?
    }
    r = requests.get(consumer_data_plane_endpoint, headers=headers)
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via CONSUMER data plane"
    j = r.json()
    print(json.dumps(j, indent=4))
    assert 'headers' in j or 'roads' in j or 'hello' in j

    end = datetime.now()
    duration = end - start
    duration_in_seconds = duration.total_seconds()
    print(f"Duration in seconds: {duration_in_seconds}")

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
