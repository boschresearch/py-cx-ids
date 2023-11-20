# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


import os
import json
import requests
import pytest
from pycxids.core.http_binding.crypto_utils import private_key_from_seed_file
from pycxids.core.http_binding.dsp_client_consumer_api import DspClientConsumerApi

from pycxids.miw.god_mode_auth_factory import GodModeAuth

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

SEED_INSECURE_FN = os.getenv('SEED_INSECURE_FN', './edc-dev-env/vault_secrets/seed.insecure')
private_key = private_key_from_seed_file(SEED_INSECURE_FN)


CONSUMER_CALLBACK_BASE_URL = os.getenv('CONSUMER_CALLBACK_BASE_URL', None)
assert CONSUMER_CALLBACK_BASE_URL, "Please set CONSUMER_CALLBACK_BASE_URL"


def god_mode_fetch(asset_id: str, bpn: str, provider_ids_endpoint: str,
                   issuer_bpn: str = "BPNL00000003CRHK",
                   their_did_prefix: str = "did:web:managed-identity-wallets-new.int.demo.catena-x.net"):
    """
    """
    auth_factory = GodModeAuth(
        bpn=bpn,
        issuer_bpn=issuer_bpn,
        our_did_prefix="did:web:miw-int.westeurope.cloudapp.azure.com",
        their_did_prefix=their_did_prefix,
        private_key=private_key,
        )

    api = DspClientConsumerApi(provider_base_url=provider_ids_endpoint, auth=auth_factory)

    catalog = api.fetch_catalog()
    catalog_str = json.dumps(catalog, indent=4)
    with open('catalog_dsp.json', 'wt') as f:
        f.write(catalog_str)
    dataset_match = []
    for dataset in catalog['dcat:dataset']:
        id = dataset.get('@id')
        if id == asset_id:
            dataset_match.append(dataset)

    assert len(dataset_match) == 1, "Could not find exactly 1 match for the restricted asset"

    offer = None
    p = dataset_match[0].get('odrl:hasPolicy')
    if isinstance(p, list):
        assert len(p) == 1, "We only support 1 policy for our tests right now"
        offer = p[0]
    else:
        offer = p

    # negotiation
    negotiation = api.negotiation(dataset_id=asset_id, offer=offer, consumer_callback_base_url=CONSUMER_CALLBACK_BASE_URL)
    print(negotiation)
    negotiation_process_id = negotiation.get('dspace:processId')
    # and now get the message from the receiver api (proprietary api)
    agreement = api.negotiation_callback_result(id=negotiation_process_id, consumer_callback_base_url=CONSUMER_CALLBACK_BASE_URL)
    print(agreement)
    agreement_id = agreement.get('dspace:agreement', {}).get('@id')
    assert agreement_id

    # transfer
    transfer = api.transfer(agreement_id_received=agreement_id, consumer_callback_base_url=CONSUMER_CALLBACK_BASE_URL)
    print(transfer)
    transfer_id = transfer.get('@id')
    transfer_process_id = transfer.get('dspace:processId')
    # EDC workaround
    correlation_id = transfer.get('dspace:correlationId')
    if correlation_id:
        transfer_process_id = correlation_id
    transfer_message = api.transfer_callback_result(id=transfer_process_id, consumer_callback_base_url=CONSUMER_CALLBACK_BASE_URL)
    assert transfer_message
    data_address = transfer_message.get('data_address')
    endpoint = data_address.get('edc:endpoint')
    auth_key = data_address.get('edc:authKey')
    auth_code = data_address.get('edc:authCode')
    assert endpoint
    assert auth_key
    assert auth_code
    headers = {
        auth_key: auth_code
    }
    r = requests.get(endpoint, headers=headers)
    assert r.status_code == 200, "Could not fetch data"
    try:
        j = r.json()
        #print(json.dumps(j, indent=4))
        return j
    except:
        data = r.content
        #print(r.content)
        return data
