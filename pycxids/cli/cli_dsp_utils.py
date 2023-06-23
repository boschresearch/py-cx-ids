#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from pycxids.cli.cli_settings import *
import requests
from uuid import uuid4
from pycxids.core.daps import Daps
from pycxids.core.http_binding.settings import DCT_FORMAT_HTTP

from pycxids.core.http_binding.models import ContractRequestMessage, OdrlOffer, TransferRequestMessage
from pycxids.utils.api import GeneralApi

class CliDspApiHelper(GeneralApi):
    def __init__(self, provider_base_url: str, daps_endpoint: str, private_key_fn: str, client_id: str) -> None:
        super().__init__(base_url=provider_base_url)
        self.daps = daps = Daps(daps_endpoint=daps_endpoint, private_key_fn=private_key_fn, client_id=client_id)
        self.headers = {}

    def update_daps_token(self, audience: str = ''):
        token = self.daps.get_daps_token(audience=audience)
        self.headers['Authorization'] = token['access_token']

    def fetch_catalog(self, out_fn: str = ''):
        data = {
            "@context":  {
                "dspace": "https://w3id.org/dspace/v0.8/"
            },
            "@type": "dspace:CatalogRequestMessage",
            "dspace:filter": {
            },

        }
        self.update_daps_token(audience=self.base_url)
        j = self.post("/catalog/request", data=data)
        return j

def get_asset_ids_from_catalog(catalog):
    datasets = catalog.get('dcat:dataset', [])
    asset_ids = []
    for d in datasets:
        dataset_id = d.get('@id')
        if dataset_id:
            asset_ids.append(dataset_id)
    return asset_ids

def get_offers_for_asset(catalog_base_url: str, asset_id: str):
    catalog_dataset_endpoint = f"{catalog_base_url}/catalog/datasets/{asset_id}"
    r = requests.get(catalog_dataset_endpoint)
    if not r.status_code == 200:
        print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
        return None
    j = r.json()
    offers = j.get('odrl:hasPolicy', [])
    return offers

def negotiation(dataset_id: str, offer: OdrlOffer, consumer_callback_base_url: str, provider_base_url: str):
    contract_request_id = str(uuid4())
    contract_request_message = ContractRequestMessage(
        field_id=contract_request_id,
        dspace_dataset=dataset_id,
        dspace_offer=offer,
        dspace_callback_address=consumer_callback_base_url,
    )
    data = contract_request_message.dict(exclude_unset=False)

    # the next step uses an internal 'requests' call that is mocked with the @patch test case annotation
    r = requests.post(f"{provider_base_url}/negotiations/request", json=data)
    if not r.status_code == 200:
        print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
        return None
    j = r.json()
    return j

def negotiation_callback_result(id: str, consumer_callback_base_url: str):
    r = requests.get(f"{consumer_callback_base_url}/negotiations/{id}/agreement")
    if not r.status_code == 200:
        print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
        return None
    j = r.json()
    return j

def transfer(agreement_id_received: str, consumer_callback_base_url: str, provider_base_url: str):
    transfer_request_id = str(uuid4())
    transfer_request_message: TransferRequestMessage = TransferRequestMessage(
        field_id = transfer_request_id,
        dspace_agreement_id = agreement_id_received,
        dct_format = DCT_FORMAT_HTTP,
        dspace_callback_address = consumer_callback_base_url,
    )
    data = transfer_request_message.dict(exclude_unset=False)
    r = requests.post(f"{provider_base_url}/transfers/request", json=data)
    if not r.status_code == 200:
        print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
        return None
    j = r.json()
    return j

def transfer_callback_result(id: str, consumer_callback_base_url: str):
    r = requests.get(f"{consumer_callback_base_url}/private/transfers/{id}")
    if not r.status_code == 200:
        print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
        return None
    j = r.json()
    return j

