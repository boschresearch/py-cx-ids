#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import click
import os
import json
import sys
from datetime import datetime
from threading import Thread
import requests
import uvicorn

from pycxids.core.ids_multipart.ids import negotiate, request_data, transfer, get_catalog
from pycxids.core.ids_multipart import webhook_fastapi
from pycxids.core import jwt_decode
from pycxids.core.ids_multipart.webhook_queue import wait_for_message
from pycxids.core.models import NotFoundException
from pycxids.core.daps import get_daps_token
from pycxids.core.settings import PROVIDER_CONNECTOR_URL, PROVIDER_CONNECTOR_IDS_ENDPOINT, endpoint_check, CONSUMER_WEBHOOK, settings

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
    daps_token = get_daps_token(audience=ids_endpoint) # TODO: handle daps error
    catalog_header, catalog = get_catalog(daps_token=daps_token, provider_connector_ids_endpoint=ids_endpoint)
    # TODO: check catalog_header for e.g. RejectionMessage, catalog is None in this case

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
    assets = set() # no double entries of assets
    for offer in catalog.get('ids:resourceCatalog', [])[0].get('ids:offeredResource', []):
        asset_prop_id = offer['ids:contractOffer'][0]['edc:policy:target']
        assets.add(asset_prop_id)
    print('\n'.join(assets))

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
    if start_webhook:
        server_thread = Thread(target=uvicorn.run, args=[webhook_fastapi.app], kwargs={'host': '0.0.0.0', 'port': settings.WEBHOOK_PORT})
        server_thread.start()

    if test_webhook:
        webhook_test = webhook_fastapi.webhook_test(CONSUMER_WEBHOOK)
        if not webhook_test:
            raise Exception('webhook not reachable. exit.')

    artifact_uri = f"urn:artifact:{asset_id}"

    catalog = fetch_catalog(connector_url)

    ids_endpoint = endpoint_check(endpoint=connector_url)
    # find contract offer for asset_id
    contract_offer = None
    for offer in catalog['ids:resourceCatalog'][0]['ids:offeredResource']: # could it be more than 1 item in the list?
        if offer['ids:contractOffer'][0]['edc:policy:target'] == asset_id: # what are the arrays here?
            contract_offer = offer
            break

    if not contract_offer:
        raise NotFoundException(f"Could not find contract offer in the catalog for asset_id: {asset_id}")

    # negotiate
    daps_token = get_daps_token(ids_endpoint)
    resource_uri = contract_offer['@id']
    agreement_header, agreement_payload = negotiate(daps_token=daps_token, contract_offer=contract_offer, provider_connector_ids_endpoint=ids_endpoint)
    
    daps_token = get_daps_token(ids_endpoint)
    transfer_header, transfer_payload = transfer(resource_uri=resource_uri, artifact_uri=artifact_uri, agreement=agreement_payload, daps_access_token=daps_token['access_token'], provider_connector_ids_endpoint=ids_endpoint)
    
    # request data, or better the EDR token
    ids_resource = transfer_payload
    daps_token = get_daps_token(ids_endpoint)
    data_request_header, data_request_payload = request_data(
        ids_resource=ids_resource,
        artifact_uri=artifact_uri,
        agreement=agreement_payload,
        daps_access_token=daps_token['access_token'],
        contract_agreement_message=agreement_header,
        provider_connector_ids_endpoint=ids_endpoint
    )
    #print(data_request_header)
    #print(data_request_payload)
    #edr_header, edr_payload = webhook_receiver_queue.get()
    #correlation_id = agreement_header['ids:transferContract']['@id']
    correlation_id = data_request_header['ids:correlationMessage']['@id']
    # now, wait for what's coming in on the webhook
    edr_header, edr_payload = wait_for_message(key=correlation_id)

    edr_json_str = json.dumps(edr_payload, indent=4)
    with(open('edr.json', 'w')) as f:
        f.write(edr_json_str)
    #print(edr_json_str)

    # actually fetch the data from the provider data plane
    headers = {
        edr_payload['authKey']: edr_payload['authCode']
    }

    decoded_auth_code = jwt_decode.decode(edr_payload['authCode'])
    """
    exp = decoded_auth_code['payload']['exp']
    now = datetime.now().timestamp()
    sec = exp - now
    min = sec/60
    print(f"seconds: {sec} minutes: {min}")
    """
    del decoded_auth_code['signature']
    edr_auth_code_str = json.dumps(decoded_auth_code, indent=4)
    with open('edr_auth_code.json', 'w') as f:
        f.write(edr_auth_code_str)

    params = {}
    endpoint = edr_payload['endpoint']
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
    """
    data_result_str = json.dumps(j, indent=4)
    with(open('data_result.json', 'w')) as f:
        f.write(data_result_str)
    #print(data_result_str)
    """
    return j

if __name__ == '__main__':
    cli()
