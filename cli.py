#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import click
import os
import sys
import json
from datetime import datetime
import base64
from uuid import uuid4
import requests
from requests.auth import HTTPBasicAuth

from pycxids.core.ids_multipart.ids_multipart import IdsMultipartConsumer
from pycxids.core.settings import endpoint_check, settings, BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD

from pycxids.utils.storage import FileStorageEngine

from pycxids.edc.settings import PROVIDER_IDS_BASE_URL

AGREEMENT_CACHE_DIR = os.getenv('AGREEMENT_CACHE_DIR', 'agreementcache')
os.makedirs(AGREEMENT_CACHE_DIR, exist_ok=True)

SETTINGS_STORAGE = os.getenv('SETTINGS_STORAGE', 'cli_settings.json')
config_storage = FileStorageEngine(storage_fn=SETTINGS_STORAGE)


@click.group('A cli to interact with IDS / EDC data providers')
def cli():
    pass

@cli.group('config', help='Configure the CLI')
def config():
    pass

@config.command('use', help='Select config to use')
@click.argument('config_name')
def cli_config_select(config_name: str):
    config_storage.put('use', config_name)

@config.command('list', help='List available configurations')
@click.argument('config_name', default='')
def cli_config_list(config_name: str):
    configs = config_storage.get('configs', {})
    if config_name:
        config = configs.get(config_name)
        print(json.dumps(config, indent=4))
    else:
        for conf in configs.keys():
            print(conf)

@config.command('add', help='Add configuration')
@click.argument('config_name')
def cli_config_add(config_name: str):
    configs = config_storage.get('configs', {})
    config = configs.get(config_name, {})

    config['PRIVATE_KEY_FN'] = click.prompt("Private key filename:",
        default=config.get('PRIVATE_KEY_FN', "private.key"))
    config['CLIENT_ID'] = click.prompt("CLIENT_ID:",
        default=config.get('CLIENT_ID', ""))
    config['DAPS_ENDPOINT'] = click.prompt("DAPS_ENDPOINT:",
        default=config.get('DAPS_ENDPOINT', "https://daps1.int.demo.catena-x.net/token"))
    config['CONSUMER_CONNECTOR_URN'] = click.prompt("CONSUMER_CONNECTOR_URN:",
        default=config.get('CONSUMER_CONNECTOR_URN', ""))
    config['CONSUMER_WEBHOOK'] = click.prompt("CONSUMER_WEBHOOK:",
        default=config.get('CONSUMER_WEBHOOK', "https://changeme.localhost/webhook"))
    config['CONSUMER_WEBHOOK_MESSAGE_BASE_URL'] = click.prompt("CONSUMER_WEBHOOK_MESSAGE_BASE_URL:",
        default=config.get('CONSUMER_WEBHOOK_MESSAGE_BASE_URL', "https://changme.localhost/messages"))
    config['CONSUMER_WEBHOOK_MESSAGE_USERNAME'] = click.prompt("CONSUMER_WEBHOOK_MESSAGE_USERNAME:",
        default=config.get('CONSUMER_WEBHOOK_MESSAGE_USERNAME', "someuser"))
    config['CONSUMER_WEBHOOK_MESSAGE_PASSWORD'] = click.prompt("CONSUMER_WEBHOOK_MESSAGE_PASSWORD (stored in clear text!):",
        default=config.get('CONSUMER_WEBHOOK_MESSAGE_PASSWORD', "somepassword"), hide_input=True, show_default=False)
    config['DEFAULT_PROVIDER_IDS_ENDPOINT'] = click.prompt("DEFAULT_PROVIDER_IDS_ENDPOINT - will be used as default if no other provider is set in specific functions:",
        default=config.get('DEFAULT_PROVIDER_IDS_ENDPOINT', "https://provider:8282/api/v1/data"))

    configs[config_name] = config
    config_storage.put('configs', configs)
    config_storage.put('use', config_name)
    click.echo("")
    click.echo("Configuration done.")
    click.echo("")

    test_webhook = click.confirm("Do you want to test the webhook?", default=True)
    if test_webhook:
        CONSUMER_WEBHOOK = config.get('CONSUMER_WEBHOOK')
        assert CONSUMER_WEBHOOK
        CONSUMER_WEBHOOK_MESSAGE_BASE_URL = config.get('CONSUMER_WEBHOOK_MESSAGE_BASE_URL')
        assert CONSUMER_WEBHOOK_MESSAGE_BASE_URL
        CONSUMER_WEBHOOK_MESSAGE_USERNAME = config.get('CONSUMER_WEBHOOK_MESSAGE_USERNAME')
        assert CONSUMER_WEBHOOK_MESSAGE_USERNAME
        CONSUMER_WEBHOOK_MESSAGE_PASSWORD = config.get('CONSUMER_WEBHOOK_MESSAGE_PASSWORD')
        assert CONSUMER_WEBHOOK_MESSAGE_PASSWORD

        test_id = str(uuid4())
        data = {'@id': test_id, 'hello': 'world'}
        r = requests.post(CONSUMER_WEBHOOK, json=data)
        assert r.ok, f"Could not post test data to WEBHOOK {CONSUMER_WEBHOOK}"

        msg_url = f"{CONSUMER_WEBHOOK_MESSAGE_BASE_URL}/{test_id}"
        r = requests.get(msg_url, json=data, auth=HTTPBasicAuth(username=CONSUMER_WEBHOOK_MESSAGE_USERNAME, password=CONSUMER_WEBHOOK_MESSAGE_PASSWORD))
        assert r.ok, f"Could not fetch test data from webhook service: {msg_url}"
        j = r.json()
        assert j.get('hello') == 'world'
        print("Successfully tested the reachability of the webhook.")


@cli.command('catalog')
@click.option('-o', '--out-fn', default='')
@click.option('--provider-ids-endpoint', default='')
def fetch_catalog_cli(provider_ids_endpoint: str, out_fn):
    if not provider_ids_endpoint:
        provider_ids_endpoint = config.get('DEFAULT_PROVIDER_IDS_ENDPOINT')
        print(f"No provider-ids-endpoint given. Using default from cli configuration: {provider_ids_endpoint}",
            file=sys.stderr) # stderr to prevent | pipe content issues
    catalog = fetch_catalog(ids_endpoint=provider_ids_endpoint, out_fn=out_fn)
    print(json.dumps(catalog, indent=4))

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
@click.option('--provider-ids-endpoint', default='')
@click.option('--agreement-id', default=None, help='Reuse existing agreement ID and save some negotiation time.')
@click.argument('asset_id', default='')
def fetch_asset_cli(provider_ids_endpoint, asset_id: str, raw_data:bool, out_dir:str, agreement_id: str):
    before = datetime.now().timestamp()

    if not provider_ids_endpoint:
        # TODO: change this
        config_to_use = config_storage.get('use')
        assert config_to_use, "Please add a config first."
        configs = config_storage.get('configs', {})
        config = configs.get(config_to_use)
        assert config, "Please add config first"
        provider_ids_endpoint = config.get('DEFAULT_PROVIDER_IDS_ENDPOINT')
        print(f"No provider-ids-endpoint given. Using default from cli configuration: {provider_ids_endpoint}",
            file=sys.stderr)

    try:
        data_result = fetch_asset(asset_id=asset_id, raw_data=raw_data, provider_ids_endpoint=provider_ids_endpoint)
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
    print(f"request duration in seconds: {duration}", file=sys.stderr)
    os._exit(1) # this does also stop the webhook thread

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
        agreement_id = cache.get(key=asset_id, default=None)
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

if __name__ == '__main__':
    cli()
