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
import requests

from pycxids.cli.cli_settings import *
from pycxids.cli import cli_multipart_utils
from pycxids.core.auth.auth_factory import DapsAuthFactory, IatpAuthFactory, MiwAuthFactory
from pycxids.core.http_binding import dsp_client_consumer_api
from pycxids.core.http_binding.models import ContractAgreementMessage, ContractNegotiation, DataAddress, EndpointProperties, EndpointPropertyNames, TransferProcess, TransferStartMessage

from pycxids.core.settings import fix_dsp_endpoint_path

from pycxids.cx.services import BdrsDirectory
from pycxids.iatp.iatp import CredentialService
from pycxids.portal.api import Portal
from pycxids.portal.settings import PORTAL_BASE_URL, PORTAL_OAUTH_TOKEN_ENDPOINT
from pycxids.utils.storage import FileStorageEngine



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

    use_dsp_iatp = click.confirm("Use (Dataspace protocol) with IATP (Identity and Trust Protocol) (product-edc 0.7.0 and higher) Y/n", default=True)
    if use_dsp_iatp:
        config['PROTOCOL'] = PROTOCOL_DSP
        config['AUTH'] = AUTH_IATP
        config['STS_CLIENT_ID'] = click.prompt("STS_CLIENT_ID:",
            default=config.get('STS_CLIENT_ID', ""))
        config['STS_CLIENT_SECRET_FN'] = click.prompt("STS_CLIENT_SECRET_FN:",
            default=config.get('STS_CLIENT_SECRET_FN', ""))
        config['STS_TOKEN_ENDPOINT'] = click.prompt("STS_TOKEN_ENDPOINT:",
            default=config.get('STS_TOKEN_ENDPOINT', ""))
        config['STS_BASE_URL'] = click.prompt("STS_BASE_URL:",
            default=config.get('STS_BASE_URL', ""))
        config['OUR_BPN'] = click.prompt("OUR_BPN:",
            default=config.get('OUR_BPN', ""))
        config['OUR_DID'] = click.prompt("OUR_DID:",
            default=config.get('OUR_DID', ""))

    use_dsp_ssi = False
    if not use_dsp_iatp:
        use_dsp_ssi = click.confirm("Use (Dataspace protocol) with SSI (Self Sovereign Identity) (product-edc 0.5.0 and higher) Y/n", default=True)
    if use_dsp_ssi:
        click.echo("Using new DSP protocol configuration (product-edc 0.4.0 and later)")
        config['PROTOCOL'] = PROTOCOL_DSP
        config['AUTH'] = AUTH_SSI
        config['MIW_CLIENT_ID'] = click.prompt("MIW_CLIENT_ID:",
            default=config.get('MIW_CLIENT_ID', ""))
        config['MIW_CLIENT_SECRET'] = click.prompt("MIW_CLIENT_SECRET (beware: stored in plain text!):",
            default=config.get('MIW_CLIENT_SECRET', ""))
        config['MIW_TOKEN_ENDPOINT'] = click.prompt("MIW_TOKEN_ENDPOINT:",
            default=config.get('MIW_TOKEN_ENDPOINT', "https://centralidp.int.demo.catena-x.net/auth/realms/CX-Central/protocol/openid-connect/token"))
        config['MIW_BASE_URL'] = click.prompt("MIW_BASE_URL",
            default=config.get('MIW_BASE_URL', "https://managed-identity-wallets-new.int.demo.catena-x.net"))
        config['CONSUMER_CONNECTOR_BASE_URL'] = click.prompt("CONSUMER_CONNECTOR_BASE_URL",
            default=config.get('CONSUMER_CONNECTOR_BASE_URL', "http://dev:6060"))
        config['DEFAULT_PROVIDER_CATALOG_BASE_URL'] = click.prompt("DEFAULT_PROVIDER_CATALOG_BASE_URL",
            default=config.get("DEFAULT_PROVIDER_CATALOG_BASE_URL", 'http://provider-control-plane:8282/api/v1/dsp'))

    use_dsp = False
    if not use_dsp_ssi or use_dsp_iatp:
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
    
    configs[config_name] = config
    config_storage.put('configs', configs)
    config_storage.put('use', config_name)
    click.echo("")
    click.echo("Configuration done. This config will be used by default now.")
    click.echo("")



def get_DspClient(provider_base_url:str, bearer_scopes: list = None, provider_did: str = None):
    """
    Depending on the setting, we return a client api with DAPS or MIW (SSI)
    """
    use_config = config_storage.get('use')
    myconfig = config_storage.get('configs', {}).get(use_config)

    auth_settings = myconfig.get('AUTH', '')
    auth_factory = None
    if auth_settings == AUTH_SSI:
        auth_factory = MiwAuthFactory(
            miw_base_url=myconfig.get('MIW_BASE_URL'),
            client_id=myconfig.get('MIW_CLIENT_ID'),
            client_secret=myconfig.get('MIW_CLIENT_SECRET'),
            token_url=myconfig.get('MIW_TOKEN_ENDPOINT')
        )
    elif auth_settings == AUTH_IATP:
        secret_fn = myconfig.get('STS_CLIENT_SECRET_FN')
        secret = ''
        with open(secret_fn, 'rt') as f:
            secret = f.read()

        auth_factory = IatpAuthFactory(
            base_url=myconfig.get('STS_BASE_URL'),
            client_id=myconfig.get('STS_CLIENT_ID'),
            client_secret=secret,
            token_url=myconfig.get('STS_TOKEN_ENDPOINT'),
            our_did=myconfig.get('OUR_DID'),
        )
    else:
        auth_factory = DapsAuthFactory(
            daps_endpoint=myconfig.get('DAPS_ENDPOINT'),
            private_key_fn=myconfig.get('PRIVATE_KEY_FN'),
            client_id=myconfig.get('CLIENT_ID'),
        )
    return dsp_client_consumer_api.DspClientConsumerApi(provider_base_url=provider_base_url, auth=auth_factory, bearer_scopes=bearer_scopes, provider_did=provider_did)

@cli.command('catalog')
@click.option('-o', '--out-fn', default='')
@click.option('--overwrite-edc-endpoint', default='')
@click.argument('bpn', default=None)
def fetch_catalog_cli(bpn: str, out_fn, overwrite_edc_endpoint: str):
    """
    For simplicity, only tractusx-edc 0.7.x and higher supported.
    """
    use_config = config_storage.get('use')
    myconfig = config_storage.get('configs', {}).get(use_config)

    protocol = myconfig.get('PROTOCOL')
    if not protocol == PROTOCOL_DSP:
        print(f"Only {PROTOCOL_DSP} protocol supported")
        return

    storage = FileStorageEngine(PARTICIPANTS_SETTINGS_CACHE)
    participant_settings = storage.get(bpn)
    edc_endpoints = participant_settings.get('edc_endpoints')
    provider_did = participant_settings.get('did')
    provider_ids_endpoint = ''
    if len(edc_endpoints) > 0:
        # TODO: what if more than 1?
        provider_ids_endpoint = edc_endpoints[0]
        if overwrite_edc_endpoint:
            provider_ids_endpoint = overwrite_edc_endpoint
    provider_ids_endpoint = fix_dsp_endpoint_path(provider_ids_endpoint)
    api = get_DspClient(provider_base_url=provider_ids_endpoint, provider_did=provider_did)

    catalog = api.fetch_catalog(out_fn=out_fn)
    catalog_str = json.dumps(catalog, indent=True)
    if out_fn:
        with open(out_fn, 'wt') as f:
            f.write(catalog_str)

    print(catalog_str)

@cli.command('catalogs', help=f"Fetch all catalogs from {PARTICIPANTS_SETTINGS_CACHE}")
@click.option('-o', '--out-dir', default='./catalogs/')
def fetch_catalogs_cli(out_dir: str):
    """
    Fetch all BPN's all endponits into the given directory
    """
    use_config = config_storage.get('use')
    myconfig = config_storage.get('configs', {}).get(use_config)

    protocol = myconfig.get('PROTOCOL')
    if not protocol == PROTOCOL_DSP:
        print(f"Only {PROTOCOL_DSP} protocol supported")
        return

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    storage = FileStorageEngine(PARTICIPANTS_SETTINGS_CACHE)
    all = storage.get_all()
    for bpn, bpn_settings in all.items():
        edc_endpoints = bpn_settings.get('edc_endpoints')
        for idx, endpoint in enumerate(edc_endpoints):
            # every BPN can have multiple EDC endpoints and thus, catalogs
            provider_did = bpn_settings.get('did')
            provider_ids_endpoint = fix_dsp_endpoint_path(endpoint)
            api = get_DspClient(provider_base_url=provider_ids_endpoint, provider_did=provider_did)

            out_fn = os.path.join(out_dir, f"{bpn}_{idx}.json")
            catalog = api.fetch_catalog()
            if not catalog:
                continue
            catalog_str = json.dumps(catalog, indent=True)
            with open(out_fn, 'wt') as f:
                f.write(catalog_str)



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
@click.option('-o', '--out-fn', default='')
@click.option('--overwrite-edc-endpoint', default='')
@click.option('--agreement-id', default=None, help='Reuse existing agreement ID and save some negotiation time.')
@click.argument('bpn', default=None)
@click.argument('dataset_id', default='')
def fetch_asset_cli(bpn: str, out_fn, overwrite_edc_endpoint: str, dataset_id: str, raw_data:bool, agreement_id: str):
    """
    For simplicity, only tractusx-edc 0.7.x and higher supported.
    """
    before = datetime.now().timestamp()

    config_to_use = config_storage.get('use')
    assert config_to_use, "Please add a config first."
    configs = config_storage.get('configs', {})
    config = configs.get(config_to_use)
    assert config, "Please add config first"

    protocol = config.get('PROTOCOL')
    if not protocol == PROTOCOL_DSP:
        print(f"Only {PROTOCOL_DSP} protocol supported")
        return

    storage = FileStorageEngine(PARTICIPANTS_SETTINGS_CACHE)
    participant_settings = storage.get(bpn)
    edc_endpoints = participant_settings.get('edc_endpoints')
    provider_did = participant_settings.get('did')
    provider_ids_endpoint = ''
    if len(edc_endpoints) > 0:
        # TODO: what if more than 1?
        provider_ids_endpoint = edc_endpoints[0]
        if overwrite_edc_endpoint:
            provider_ids_endpoint = overwrite_edc_endpoint
    provider_ids_endpoint = fix_dsp_endpoint_path(provider_ids_endpoint)
    api = get_DspClient(provider_base_url=provider_ids_endpoint, provider_did=provider_did)

    offers = api.get_offers_for_dataset(dataset_id=dataset_id)
    print(offers)
    consumer_callback_base_url = config.get('CONSUMER_CONNECTOR_BASE_URL')
    consumer_callback_base_url = "http://dev:12000"
    # TODO catalog_base_url should not be used here, but rather the endpoint from the catalog result!
    negotiation:ContractNegotiation = api.negotiation(dataset_id=dataset_id, offer=offers[0], consumer_callback_base_url=consumer_callback_base_url)
    print(negotiation)
    # and now get the message from the receiver api (proprietary api)
    agreement_message:ContractAgreementMessage = api.negotiation_callback_result(id=negotiation.dspace_consumer_pid, consumer_callback_base_url=consumer_callback_base_url)
    print(agreement_message)
    assert agreement_message.dspace_agreement.field_id, "No agreement ID."
    assert agreement_message.dspace_consumer_pid == negotiation.dspace_consumer_pid, "Agreement and Negoation consumePid not equal!"
    transfer:TransferProcess = api.transfer(agreement_id_received=agreement_message.dspace_agreement.field_id, consumer_pid=agreement_message.dspace_consumer_pid, consumer_callback_base_url=consumer_callback_base_url)
    print(transfer)
    transfer_start_message:TransferStartMessage = api.transfer_callback_result(id=transfer.dspace_consumer_pid, consumer_callback_base_url=consumer_callback_base_url)
    assert transfer_start_message
    print(transfer_start_message)

    data_address_received: DataAddress = transfer_start_message.dspace_data_address

    authorization = dsp_client_consumer_api.DspClientConsumerApi.get_data_address_authorization(data_address_received)
    endpoint = dsp_client_consumer_api.DspClientConsumerApi.get_data_address_endpoint(data_address_received)

    assert authorization, "Could not find authorization token in DataAddress properties."
    assert endpoint, "Could not find endpoint in DataAddress properties."
    # actual request of the data
    headers = {
        "Authorization": authorization
    }
    r = requests.get(endpoint, headers=headers)
    if raw_data:
        data_result = r.content
    else:
        data_result = r.json()

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
    if out_fn:
        with(open(out_fn, 'w')) as f:
            f.write(data_str)
    else:
        print(data_str)
    print(f"request duration in seconds: {duration}", file=sys.stderr)
    os._exit(1) # this does also stop the webhook thread


@cli.command('update', help='Only from 0.7.x onwards')
@click.option('-o', '--out', help='Filename for output.', default=PARTICIPANTS_SETTINGS_CACHE)
@click.option('--client_id', default='', help='Portal technical user with discovery role')
@click.option('--client_secret_fn', default='.secrets/discovery.secret', help='Filename with corresponding client_secret')
@click.option('--token_endpoint', default=PORTAL_OAUTH_TOKEN_ENDPOINT, help='Filename with corresponding client_secret')
@click.option('--portal_base_url', default=PORTAL_BASE_URL, help='Portal base URL')
def update_participant_settings_cli(out, client_id, client_secret_fn, token_endpoint, portal_base_url):
    c = get_DspClient("")
    token = c.auth.get_token(aud="")
    # use our own token to read our own CS content
    cs = CredentialService(credential_service_base_url=CredentialService.INT_TESTING_DIM, access_token=token)
    vps = cs.get_vps()

    # BDRS (BPN - DID Mapping)
    bdrs = BdrsDirectory(bdrs_base_url=BdrsDirectory.BDRS_INT, membership_vp_jwt=vps[0])
    bpn_mappings = bdrs.get_directory()
    #print(json.dumps(bpn_mappings, indent=True))

    # Find all EDC endpoints
    portal_secret = ''
    with open(client_secret_fn, 'rt') as f:
        portal_secret=f.read()
    portal = Portal(portal_base_url=PORTAL_BASE_URL, token_url=PORTAL_OAUTH_TOKEN_ENDPOINT, client_id="sa194", client_secret=portal_secret)

    storage = FileStorageEngine(PARTICIPANTS_SETTINGS_CACHE)
    for bpn, did in bpn_mappings.items():
        edc_endpoints = portal.discover_edc_endpoint(bpn=bpn)
        x = {
            "did": did,
            "edc_endpoints": edc_endpoints
        }
        storage.put(bpn, x)


if __name__ == '__main__':
    cli()
