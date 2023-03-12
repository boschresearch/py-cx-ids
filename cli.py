#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import click
import os
import json
from datetime import datetime
import requests

from pycxids.core.ids_multipart.ids_multipart import IdsMultipartConsumer
from pycxids.core.settings import endpoint_check, settings, BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD

from pycxids.edc.settings import PROVIDER_IDS_BASE_URL

@click.group('A cli to interact with IDS / EDC data providers')
def cli():
    pass

@cli.command('catalog')
@click.option('-o', '--out-fn', default='')
@click.argument('provider_connector_url', default=PROVIDER_IDS_BASE_URL)
def fetch_catalog_cli(provider_connector_url: str, out_fn):
    catalog = fetch_catalog(endpoint=provider_connector_url, out_fn=out_fn)
    print(json.dumps(catalog, indent=4))

def fetch_catalog(endpoint: str, out_fn: str = ''):
    """
    Fetch the catalog from the given endpoint.

    Returns None in case of an error
    """
    ids_endpoint = endpoint_check(endpoint=endpoint)

    consumer = IdsMultipartConsumer(
        private_key_fn=settings.PRIVATE_KEY_FN,
        provider_connector_ids_endpoint=ids_endpoint,
        consumer_connector_urn=settings.CONSUMER_CONNECTOR_URN,
        consumer_connector_webhook_url='http://dev:6080/webhook',
        consumer_webhook_message_base_url='http://dev:6080/messages',
        consumer_webhook_message_username=BASIC_AUTH_USERNAME,
        consumer_webhook_message_password=BASIC_AUTH_PASSWORD,
    )

    catalog = consumer.get_catalog()

    if out_fn:
        os.makedirs(os.path.dirname(out_fn), exist_ok=True)
        catalog_str = json.dumps(catalog, indent=4)
        with open(out_fn, 'w') as f:
            f.write(catalog_str)

    return catalog

@cli.command('assets', help="List asset:prop:id list from a given catalog via filename or stdin")
@click.argument('catalog_filename', default='')
def list_assets_from_catalog(catalog_filename: str):
    catalog_str = ''
    if catalog_filename:
        # read catalog content from file
        if os.path.isfile(catalog_filename):
            with(open(catalog_filename, 'r')) as f:
                catalog_str = f.read()
    else:
        # stdtin case
        catalog_str = click.get_text_stream('stdin').read().strip()

    catalog = json.loads(catalog_str)
    asset_ids = IdsMultipartConsumer.get_asset_ids_from_catalog(catalog=catalog)
    print('\n'.join(asset_ids))

@cli.command('fetch', help="Fetch a given asset id")
@click.option('-r', '--raw-data', default=False, is_flag=True)
@click.option('--out-dir', default='', help='Directory in which the results should be stored under the asset_id filename.')
@click.option('--provider-connector-url', default=PROVIDER_IDS_BASE_URL)
@click.argument('asset_id', default='')
def fetch_asset_cli(provider_connector_url, asset_id: str, raw_data:bool, out_dir:str):
    before = datetime.now().timestamp()
    try:
        data_result = fetch_asset(asset_id=asset_id, raw_data=raw_data, connector_url=provider_connector_url)
    except Exception as ex:
        print(ex)
        os._exit(1) # this is a first class cli function, here we can immediately exit
    after = datetime.now().timestamp()
    duration = after - before
    data_str = None
    if raw_data:
        data_str = data_result
    else:
        data_str = json.dumps(data_result, indent=4)
    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        fn = os.path.join(out_dir, asset_id) # raw data, no ending
        if not raw_data:
            fn = fn + '.json'
        with(open(fn, 'w')) as f:
            f.write(data_str)
    else:
        print(data_str)
    print(f"request duration in seconds: {duration}")
    os._exit(1) # this does also stop the webhook thread

def fetch_asset(asset_id: str, raw_data: bool = False, start_webhook=True, test_webhook=False, connector_url=None, suburl=None, query_params=None):
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

    ids_endpoint = endpoint_check(endpoint=connector_url)

    consumer = IdsMultipartConsumer(
        private_key_fn=settings.PRIVATE_KEY_FN,
        provider_connector_ids_endpoint=ids_endpoint,
        consumer_connector_urn=settings.CONSUMER_CONNECTOR_URN,
        consumer_connector_webhook_url='http://dev:6080/webhook',
        consumer_webhook_message_base_url='http://dev:6080/messages',
        consumer_webhook_message_username=BASIC_AUTH_USERNAME,
        consumer_webhook_message_password=BASIC_AUTH_PASSWORD,
    )

    # find offers from the catalog
    offers = consumer.get_offers(asset_id=asset_id)
    offer = offers[0] # TODO: check which offer to use
    # negotiate
    agreement_id = consumer.negotiate(contract_offer=offer)
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

if __name__ == '__main__':
    cli()
