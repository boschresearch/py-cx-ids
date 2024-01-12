# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


from copy import deepcopy
from time import sleep
import json
from uuid import uuid4
import pytest
from datetime import datetime

from pycxids.edc.api import EdcConsumer, EdcProvider
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, PROVIDER_IDS_ENDPOINT, RECEIVER_SERVICE_BASE_URL
from pycxids.edc.settings import DUMMY_BACKEND

from pycxids.core.settings import settings

CONSUMER_BPN = 'BPNLconsumer'
NUMBER_OF_ASSETS = 1000

def test():
    """
    Test if there is an issue with 'higher' number of contracts
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    asset_base_id = str(uuid4())

    for i in range(0, NUMBER_OF_ASSETS):
        asset_id = f"{asset_base_id}_{i}"
        asset_id_created = provider.create_asset(asset_id=asset_id ,base_url=DUMMY_BACKEND)
        assert asset_id == asset_id_created

        policy_id = f"{asset_id}_policy"
        policy_id_created = provider.create_policy(asset_id=asset_id, policy_id=policy_id)
        assert policy_id == policy_id_created

        contract_id = provider.create_contract_definition(policy_id=policy_id, asset_id=asset_id)
        assert contract_id

    sleep(1)

    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url=RECEIVER_SERVICE_BASE_URL,
        )

    duration_seconds_sum = 0.0
    for i in range(0, NUMBER_OF_ASSETS):
        start = datetime.now()
        asset_id = f"{asset_base_id}_{i}"
        catalog = consumer.get_dataset(dataset_id=asset_id, provider_ids_endpoint=PROVIDER_IDS_ENDPOINT)
        assert catalog
        datasets = catalog.get('dcat:dataset', [])
        assert len(datasets) == 1, "Could not fetch exactly 1 dataset"
        dataset = datasets[0]
        contract_offer = dataset.get('odrl:hasPolicy')
        assert isinstance(contract_offer, list) == False

        edr_init = consumer.edr_start_process(
            provider_ids_endpoint=PROVIDER_IDS_ENDPOINT,
            contract_offer=contract_offer,
            asset_id=asset_id,
            provider_participant_id=settings.PROVIDER_PARTICIPANT_ID,
        )
        negotiation_id = edr_init.get('@id')
        consumer_edr = consumer.edr_for_negotiation(negotiation_id=negotiation_id)

        assert consumer_edr, "Could not fetch consumer_edr from receiver service."
        end = datetime.now()
        duration = end - start
        duration_in_seconds = duration.total_seconds()
        print(f"neogotation in seconds: {duration_in_seconds}")
        duration_seconds_sum = duration_seconds_sum + duration_in_seconds
        avg = duration_seconds_sum / (i +1)
        print(f"duration in seconds average: {avg}")


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
