# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


from copy import deepcopy
from time import sleep
import json
import pytest

from pycxids.edc.api import EdcConsumer, EdcProvider
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, PROVIDER_IDS_ENDPOINT, RECEIVER_SERVICE_BASE_URL
from pycxids.edc.settings import DUMMY_BACKEND


test_odrl_constraint = [
    {
        "odrl:leftOperand": "FrameworkAgreement.traceability",
        "odrl:operator": {
            "@id": "odrl:eq"
        },
        "odrl:rightOperand": "active"
    }
]

CONSUMER_BPN = 'BPNLConsumer'
CONSUMER_BPN = 'BPNL00000003B5MJ'

def test():
    """
    Test a few things with access policies, e.g. can we gernally see what we define in access policies
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    asset_id_consumer = provider.create_asset(base_url=DUMMY_BACKEND)
    asset_id_xxx = provider.create_asset(base_url=DUMMY_BACKEND)

    access_policy_consumer = provider.create_access_policy(bpn=CONSUMER_BPN)
    access_policy_xxx = provider.create_access_policy(bpn='xxx')

    odrl_constraint_1 = deepcopy(test_odrl_constraint)

    policy_id_consumer = provider.create_policy(asset_id=asset_id_consumer)
    policy_id_xxx = provider.create_policy(asset_id=asset_id_xxx)

    contract_id_consumer = provider.create_contract_definition(policy_id=policy_id_consumer, asset_id=asset_id_consumer, access_policy_id=access_policy_consumer)
    contract_id_xxx = provider.create_contract_definition(policy_id=policy_id_xxx, asset_id=asset_id_xxx, access_policy_id=access_policy_xxx)

    assert contract_id_consumer
    assert contract_id_xxx

    sleep(1)

    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url=RECEIVER_SERVICE_BASE_URL,
        )
    catalog = consumer.get_catalog(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT)
    assert catalog
    with open(__file__ + '.json', 'wt') as f:
        f.write(json.dumps(catalog, indent=4))
    dataset_consumer = None
    for dataset in catalog['dcat:dataset']:
        if dataset['@id'] == asset_id_consumer:
            dataset_consumer = dataset
            break

    dataset_xxx = None
    for dataset in catalog['dcat:dataset']:
        if dataset['@id'] == asset_id_xxx:
            dataset_xxx = dataset
            break

    assert dataset_consumer, "We can't see the consumer dataset, but we should"
    assert dataset_xxx == None, "We can see the xxx dataset, but we shouldn't"

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
