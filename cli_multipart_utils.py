#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from cli_settings import *
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