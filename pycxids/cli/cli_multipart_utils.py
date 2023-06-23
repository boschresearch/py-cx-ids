#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import requests
import sys
import json
import base64
from pycxids.cli.cli_settings import *
from pycxids.core.ids_multipart.ids_multipart import IdsMultipartConsumer


def get_consumer(ids_endpoint: str):
    """
    Returns a consumer instance created from settings
    """

    config_to_use = config_storage.get('use', None)
    assert config_to_use, "Please add a config first"
    print(f"Using {config_to_use}", file=sys.stderr)
    configs = config_storage.get('configs', {})
    config = configs.get(config_to_use, None)
    assert config, f"Please configure {config_to_use} first."

    consumer = IdsMultipartConsumer(
        private_key_fn=config.get('PRIVATE_KEY_FN'),
        client_id=config.get('CLIENT_ID'),
        daps_endpoint=config.get('DAPS_ENDPOINT'),
        provider_connector_ids_endpoint=ids_endpoint,
        consumer_connector_urn=config.get('CONSUMER_CONNECTOR_URN'),
        consumer_connector_webhook_url=config.get('CONSUMER_WEBHOOK'),
        consumer_webhook_message_base_url=config.get('CONSUMER_WEBHOOK_MESSAGE_BASE_URL'),
        consumer_webhook_message_username=config.get('CONSUMER_WEBHOOK_MESSAGE_USERNAME'),
        consumer_webhook_message_password=config.get('CONSUMER_WEBHOOK_MESSAGE_PASSWORD'),
    )
    return consumer

def fetch_catalog(ids_endpoint: str, out_fn: str = ''):
    """
    Fetch the catalog from the given endpoint.

    Returns None in case of an error
    """
    consumer = get_consumer(ids_endpoint=ids_endpoint)

    catalog = consumer.get_catalog()

    if out_fn:
        os.makedirs(os.path.dirname(out_fn), exist_ok=True)
        catalog_str = json.dumps(catalog, indent=4)
        with open(out_fn, 'w') as f:
            f.write(catalog_str)

    return catalog

def get_asset_ids_from_catalog(catalog):
    asset_ids = IdsMultipartConsumer.get_asset_ids_from_catalog(catalog=catalog)
    return asset_ids

def fetch_asset(asset_id: str, raw_data: bool = False, start_webhook=True, test_webhook=False, provider_ids_endpoint=None, suburl=None, query_params=None, agreement_id:str = None):
    """
    Starts the webhook to receive async messages
    Does the negotiation with the provider control plane and the actual data fetch from the provider data plane.
    """

    """
    if start_webhook:
        server_thread = Thread(target=uvicorn.run, args=[webhook_fastapi.app], kwargs={'host': '0.0.0.0', 'port': settings.WEBHOOK_PORT})
        server_thread.start()

    if test_webhook:
        webhook_test = webhook_fastapi.webhook_test(CONSUMER_WEBHOOK)
        if not webhook_test:
            raise Exception('webhook not reachable. exit.')
    """

    ids_endpoint = provider_ids_endpoint
    ids_endpoint_b64 = base64.urlsafe_b64encode(ids_endpoint.encode()).decode()
    cache_fn = os.path.join(AGREEMENT_CACHE_DIR, ids_endpoint_b64)
    cache = FileStorageEngine(storage_fn=cache_fn)

    consumer = get_consumer(ids_endpoint=ids_endpoint)

    if not agreement_id:
        # if not given, next lookup in cache
        # disable cache for now - until we know when to clean it up
        # agreement_id = cache.get(key=asset_id, default=None)
        if not agreement_id:
            # find offers from the catalog
            offers = consumer.get_offers(asset_id=asset_id)
            offer = offers[0] # TODO: check which offer to use
            # negotiate
            agreement_id = consumer.negotiate(contract_offer=offer)
            # and cache it for later
            cache.put(key=asset_id, value=agreement_id)
    # transfer
    provider_edr = consumer.transfer(asset_id=asset_id, agreement_id=agreement_id)

    # actually fetch the data from the provider data plane
    headers = {
        provider_edr.get('authKey'): provider_edr.get('authCode')
    }

    params = {}
    endpoint = provider_edr.get('endpoint')
    if not raw_data:
        if suburl:
            endpoint = endpoint + '/' + suburl
        else:
            endpoint = endpoint + '/submodel'
        if query_params:
            params = query_params
        else:
            params['content'] = 'value'
            params['extent'] = 'withBlobValue'
    else:
        # data plane trailing '/' bug workaround
        # https://github.com/eclipse-edc/Connector/issues/2242
        if not endpoint.endswith('/'):
            endpoint = endpoint + '/'
    r = requests.get(endpoint, headers=headers, params=params)
    if not r.ok:
        print(r.content)
        return None
    if raw_data:
        content = r.content
        with(open('data_result_raw.txt', 'wb')) as f:
            f.write(content)
        return content

    j = r.json()
    return j
