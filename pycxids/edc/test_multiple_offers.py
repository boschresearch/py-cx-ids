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


def test():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    asset_id = provider.create_asset(base_url=DUMMY_BACKEND)
    odrl_constraint_1 = deepcopy(test_odrl_constraint)
    odrl_constraint_1['odrl:and'][0]['odrl:leftOperand'] = "policy_1." + asset_id
    policy_id = provider.create_policy(asset_id=asset_id, odrl_constraint=odrl_constraint_1)
    odrl_constraint_2 = deepcopy(test_odrl_constraint)
    odrl_constraint_2['odrl:and'][0]['odrl:leftOperand'] = "policy_2." + asset_id
    policy_id_2 = provider.create_policy(asset_id=asset_id, odrl_constraint=odrl_constraint_2)

    contract_id = provider.create_contract_definition(policy_id=policy_id, asset_id=asset_id)
    contract_id_2 = provider.create_contract_definition(policy_id=policy_id_2, asset_id=asset_id)
    assert contract_id
    assert contract_id_2

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
    our_dataset = None
    for dataset in catalog['dcat:dataset']:
        if dataset['@id'] == asset_id:
            our_dataset = dataset
            break

    offers = our_dataset.get('odrl:hasPolicy')
    assert offers, "Dataset does not provide any offer"
    assert isinstance(offers, list), "odrl:hasPolicy / offers are not a list"
    assert len(offers) == 2, "Number of offers not correct"


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
