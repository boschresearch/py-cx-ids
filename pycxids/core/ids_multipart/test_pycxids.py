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


def test_catlog_filter():
    """
    """
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    backend_endpoint = 'http://dummy-backend:8000/returnparams'
    asset_id, policy_id, contract_id = provider.create_asset_and_friends(base_url=backend_endpoint, proxyPath=True)

    assert asset_id, "Could not create asset"
    assert policy_id, "Could not create policy"
    assert contract_id, "Could not crate contract definition"

    # we need at least 2 assets for our test
    asset_id_2, policy_id_2, contract_id_2 = provider.create_asset_and_friends(base_url=backend_endpoint, proxyPath=True)

    assert asset_id_2, "Could not create asset"
    assert policy_id_2, "Could not create policy"
    assert contract_id_2, "Could not crate contract definition"

    sleep(1)
    # Consumer
    consumer = IdsMultipartConsumer(
        private_key_fn='./edc-dev-env/vault_secrets/consumer.key',
        provider_connector_ids_endpoint='http://provider-control-plane:8282/api/v1/ids/data',
        consumer_connector_urn='urn:uuid:consumer',
        consumer_connector_webhook_url='http://dev:6080/webhook',
        consumer_webhook_message_base_url='http://dev:6080/messages',
        consumer_webhook_message_username='someuser',
        consumer_webhook_message_password='somepassword',
    )
    offers = consumer.get_offers(asset_id=asset_id)


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
