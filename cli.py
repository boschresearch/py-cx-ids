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

from pycxids.cli.cli_settings import *
from pycxids.cli import cli_multipart_utils
from pycxids.core.auth.auth_factory import DapsAuthFactory
from pycxids.core.http_binding import dsp_client_consumer_api
from pycxids.core.http_binding.models_local import DataAddress, TransferStateStore

from pycxids.core.settings import endpoint_check, settings, BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD

from pycxids.utils.storage import FileStorageEngine

from pycxids.edc.settings import PROVIDER_IDS_BASE_URL



@click.group('A cli to interact with IDS / EDC data providers')
def cli():
    pass

@cli.group('config', help='Configure the CLI')
def config():
    pass

@config.command('use', help='Select config to use')
@click.argument('config_name', default='')
def cli_config_select(config_name: str):
    if config_name:
        config_storage.put('use', config_name)
    else:
        config_name = config_storage.get('use')
        print(config_name)

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

    use_dsp = click.confirm("Use new DSP (Dataspace protocol) version? (product-edc 0.4.0 and higher) Y/n", default=True)
    if use_dsp:
        click.echo("Using new DSP protocol configuration (product-edc 0.4.0 and later)")
        config['PROTOCOL'] = PROTOCOL_DSP
        config['PRIVATE_KEY_FN'] = click.prompt("Private key filename:",
            default=config.get('PRIVATE_KEY_FN', "private.key"))
        config['CLIENT_ID'] = click.prompt("CLIENT_ID:",
            default=config.get('CLIENT_ID', ""))
        config['DAPS_ENDPOINT'] = click.prompt("DAPS_ENDPOINT:",
            default=config.get('DAPS_ENDPOINT', "https://daps1.int.demo.catena-x.net/token"))
        config['CONSUMER_CONNECTOR_BASE_URL'] = click.prompt("CONSUMER_CONNECTOR_BASE_URL",
            default=config.get('CONSUMER_CONNECTOR_BASE_URL', "http://localhost:6060"))
        config['DEFAULT_PROVIDER_CATALOG_BASE_URL'] = click.prompt("DEFAULT_PROVIDER_CATALOG_BASE_URL",
            default=config.get("DEFAULT_PROVIDER_CATALOG_BASE_URL", "http://localhost:8080"))
    else:
        click.echo("Using old multipart protocol configuration (before product-edc 0.4.0)")
        config['PROTOCOL'] = PROTOCOL_MULTIPART
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
    click.echo("Configuration done. This config will be used by default now.")
    click.echo("")

    if not use_dsp:
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

def get_DSP_api_helper(provider_base_url:str):
    use_config = config_storage.get('use')
    myconfig = config_storage.get('configs', {}).get(use_config)

    daps_auth_factory = DapsAuthFactory(
        daps_endpoint=myconfig.get('DAPS_ENDPOINT'),
        private_key_fn=myconfig.get('PRIVATE_KEY_FN'),
        client_id=myconfig.get('CLIENT_ID'),
    )
    return dsp_client_consumer_api.DspClientConsumerApi(provider_base_url=provider_base_url, auth=daps_auth_factory)

@cli.command('catalog')
@click.option('-o', '--out-fn', default='')
@click.option('--provider-ids-endpoint', default='', help='IDS endpoint in multipart or catalog endpoint in DSP')
def fetch_catalog_cli(provider_ids_endpoint: str, out_fn):
    use_config = config_storage.get('use')
    myconfig = config_storage.get('configs', {}).get(use_config)

    protocol = myconfig.get('PROTOCOL')
    if protocol == PROTOCOL_DSP:
        if not provider_ids_endpoint:
            provider_base_url = myconfig.get('DEFAULT_PROVIDER_CATALOG_BASE_URL')
        else:
            provider_base_url = provider_ids_endpoint

        api = get_DSP_api_helper(provider_base_url=provider_base_url)

        catalog = api.fetch_catalog(out_fn=out_fn)
        print(json.dumps(catalog, indent=4))

    else:
        if not provider_ids_endpoint:
            provider_ids_endpoint = myconfig.get('DEFAULT_PROVIDER_IDS_ENDPOINT')
            print(f"No provider-ids-endpoint given. Using default from cli configuration: {provider_ids_endpoint}",
                file=sys.stderr) # stderr to prevent | pipe content issues
        catalog = cli_multipart_utils.fetch_catalog(ids_endpoint=provider_ids_endpoint, out_fn=out_fn)
        print(json.dumps(catalog, indent=4))


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
    asset_ids = None
    # check if DSP catalog result:
    datasets = catalog.get('dcat:dataset', None)
    if datasets:
        # DSP case
        asset_ids = dsp_client_consumer_api.DspClientConsumerApi.get_asset_ids_from_catalog(catalog=catalog)
    else:
        asset_ids = cli_multipart_utils.get_asset_ids_from_catalog(catalog=catalog)
    print('\n'.join(asset_ids))

@cli.command('fetch', help="Fetch a given asset id")
@click.option('-r', '--raw-data', default=False, is_flag=True)
@click.option('--out-dir', default='', help='Directory in which the results should be stored under the asset_id filename.')
@click.option('--provider-ids-endpoint', default='')
@click.option('--agreement-id', default=None, help='Reuse existing agreement ID and save some negotiation time.')
@click.argument('asset_id', default='')
def fetch_asset_cli(provider_ids_endpoint, asset_id: str, raw_data:bool, out_dir:str, agreement_id: str, help="IDS endpoint or DSP catalog BASE URL"):
    before = datetime.now().timestamp()

    config_to_use = config_storage.get('use')
    assert config_to_use, "Please add a config first."
    configs = config_storage.get('configs', {})
    config = configs.get(config_to_use)
    assert config, "Please add config first"

    if config.get('PROTOCOL', '') == PROTOCOL_DSP:
        provider_base_url = ''
        if not provider_ids_endpoint:
            provider_base_url = config.get('DEFAULT_PROVIDER_CATALOG_BASE_URL')
        api = get_DSP_api_helper(provider_base_url=provider_base_url)
        offers = api.get_offers_for_asset(asset_id=asset_id)
        print(offers)
        consumer_callback_base_url = config.get('CONSUMER_CONNECTOR_BASE_URL')
        # TODO catalog_base_url should not be used here, but rather the endpoint from the catalog result!
        negotiation = api.negotiation(dataset_id=asset_id, offer=offers[0], consumer_callback_base_url=consumer_callback_base_url, provider_base_url=provider_base_url)
        print(negotiation)
        negotiation_process_id = negotiation.get('dspace:processId')
        # and now get the message from the receiver api (proprietary api)
        agreement = api.negotiation_callback_result(id=negotiation_process_id, consumer_callback_base_url=consumer_callback_base_url)
        print(agreement)
        agreement_id = agreement.get('@id')
        transfer = api.transfer(agreement_id_received=agreement_id, consumer_callback_base_url=consumer_callback_base_url, provider_base_url=provider_base_url)
        print(transfer)
        transfer_id = transfer.get('@id')
        transfer_process_id = transfer.get('dspace:processId')
        transfer_message = api.transfer_callback_result(id=transfer_process_id, consumer_callback_base_url=consumer_callback_base_url)
        print(transfer_message)
        transfer_state_received = TransferStateStore.parse_obj(transfer_message)
        data_address_received: DataAddress = transfer_state_received.data_address
        # actual request of the data
        headers = {
            data_address_received.auth_key: data_address_received.auth_code
        }
        r = requests.get(data_address_received.base_url, headers=headers)
        data_result = r.content
        #print(data_result)

    else:
        if not provider_ids_endpoint:
            # TODO: change this
            provider_ids_endpoint = config.get('DEFAULT_PROVIDER_IDS_ENDPOINT')
            print(f"No provider-ids-endpoint given. Using default from cli configuration: {provider_ids_endpoint}",
                file=sys.stderr)

        try:
            data_result = cli_multipart_utils.fetch_asset(asset_id=asset_id, raw_data=raw_data, provider_ids_endpoint=provider_ids_endpoint)
        except Exception as ex:
            print(ex)
            os._exit(1) # this is a first class cli function, here we can immediately exit
    after = datetime.now().timestamp()
    duration = after - before
    data_str = None
    if raw_data:
        data_str = data_result
    else:
        try:
            data_str = json.dumps(data_result, indent=4)
        except Exception as ex:
            data_str = data_result
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


if __name__ == '__main__':
    cli()
