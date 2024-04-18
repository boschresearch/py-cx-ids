# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from pycxids.edc.api import EdcConsumer
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, RECEIVER_SERVICE_BASE_URL
from pycxids.core.settings import settings


def test():
    """
    """
    asset_id = 'demo_asset'
    provider_base_url = 'http://dev:8080' # needs to be started separately
    provider_ids_endpoint = f"{provider_base_url}"

    consumer = EdcConsumer(
        edc_data_managment_base_url=CONSUMER_EDC_BASE_URL,
        auth_key=CONSUMER_EDC_API_KEY,
        token_receiver_service_base_url=RECEIVER_SERVICE_BASE_URL,
        )

    catalog = consumer.get_catalog(provider_ids_endpoint=provider_ids_endpoint)
    contract_offer = consumer.find_first_in_catalog(catalog=catalog, asset_id=asset_id)
    assert contract_offer, "Could not find matching offer in catalog"

    provider_edc_participant_id = catalog.get('edc:participantId')
    assert provider_edc_participant_id, "Could not find edc:participantId from received catalog result"

    negotiated_contract = consumer.negotiate_contract_and_wait(provider_ids_endpoint=provider_ids_endpoint,
        contract_offer=contract_offer, asset_id=asset_id,
        provider_participant_id=provider_edc_participant_id,
        consumer_participant_id=settings.CONSUMER_PARTICIPANT_ID,
        timeout=60
        )

    # test call via CONSUMER data plane
    consumer_edr = consumer.edr_consumer_wait(transfer_id=transfer_id)
    consumer_data_plane_endpoint = consumer_edr.get('endpoint')
    r = requests.get(consumer_data_plane_endpoint, headers={consumer_edr['authKey']: consumer_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via CONSUMER data plane"
    j = r.json()
    assert 'agreement_id' in j

    # test call directly against the PROVIDER
    provider_edr = consumer.edr_provider_wait(transfer_id=transfer_id)
    provider_data_plane_endpoint = provider_edr.get('baseUrl')
    r = requests.get(provider_data_plane_endpoint, headers={provider_edr['authKey']: provider_edr['authCode']})
    if not r.ok:
        print(f"{r.status_code} {r.reason} {r.content}")
        assert False, "Could not fetch data via PROVIDER data plane"
    j = r.json()
    assert 'agreement_id' in j

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
