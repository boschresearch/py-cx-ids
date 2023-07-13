#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import sys
from pycxids.cli.cli_settings import *
import requests
from uuid import uuid4
from pycxids.core.auth.auth_factory import AuthFactory
from pycxids.utils.helper import print_red
from pycxids.core.daps import Daps
from pycxids.core.http_binding.settings import DCT_FORMAT_HTTP

from pycxids.core.http_binding.models import ContractRequestMessage, OdrlOffer, TransferRequestMessage
from pycxids.utils.api import GeneralApi

class DspClientConsumerApi(GeneralApi):
    def __init__(self, provider_base_url: str, auth: AuthFactory) -> None:
        super().__init__(base_url=provider_base_url)
        self.auth = auth
        self.headers = {}
        self._update_auth_token()

    def _update_auth_token(self):
        token = self.auth.get_token(aud=self.base_url) # audience is always only the base_url
        self.headers['Authorization'] = token

    def fetch_catalog(self, out_fn: str = '', filter: dict = None):
        data = {
            "@context":  {
                "dspace": "https://w3id.org/dspace/v0.8/"
            },
            "@type": "dspace:CatalogRequestMessage",
            "dspace:filter": {
            },

        }
        if filter:
            data['dspace:filter'] = filter
        self._update_auth_token()
        j = self.post("/catalog/request", data=data)
        dataset = j.get('dcat:dataset')
        if not isinstance(dataset, list):
            # EDC bug workaround: https://github.com/eclipse-edc/Connector/issues/3232
            j['dcat:dataset'] = [dataset]
        return j

    @classmethod
    def get_asset_ids_from_catalog(cls, catalog):
        datasets = catalog.get('dcat:dataset', [])
        asset_ids = []
        for d in datasets:
            dataset_id = d.get('@id')
            # workaround because edc generates new dataset_id for every request :-(
            edc_id = d.get('edc:id')
            if edc_id:
                print(f"Warning: Using edc:id instead of datasetId. dataset_id: {dataset_id} edc_id: {edc_id}", file=sys.stderr)
                dataset_id = edc_id
            if dataset_id:
                asset_ids.append(dataset_id)
        return asset_ids

    @classmethod
    def get_dataset_from_catalog(cls, catalog, asset_id: str):
        """
        Because of limits in filtering for an asset in EDC (product-edc 0.4.1)
        """
        datasets = catalog.get('dcat:dataset', [])
        for d in datasets:
            dataset_id = d.get('@id')
            edc_id = d.get('edc:id')
            if dataset_id == asset_id:
                return d
            if edc_id == asset_id:
                return d
        return None

    def get_offers_for_asset(self, asset_id: str):
        """
        Get the offers from a given asset / dataset
        """
        catalog_dataset_endpoint = f"/catalog/datasets/{asset_id}"
        #r = self.get(catalog_dataset_endpoint)
        self._update_auth_token()
        r = requests.get(f"{self.base_url}{catalog_dataset_endpoint}", headers=self.headers)
        if r.status_code == 404:
            # this is probably the missing endpoint in EDC use a workaround for now
            # https://github.com/eclipse-edc/Connector/issues/3220
            filtered_catalog = self.get_catalog_edc_workaround(asset_id=asset_id)
            dataset = filtered_catalog.get('dcat:dataset')
            if len(dataset) > 1:
                print(f"Error: filtered catalog result should only contain 1 element, but contains more. asset_id: {asset_id}", file=sys.stderr)
                print(f"Using first!", file=sys.stderr)
            dataset = dataset[0]                

            policies = dataset.get('odrl:hasPolicy', [])
            # EDC workaround https://github.com/eclipse-edc/Connector/issues/3233
            if not isinstance(policies, list):
                policies = [policies]
            return policies
            # catalog = self.fetch_catalog()
            # dataset = CliDspApiHelper.get_dataset_from_catalog(catalog=catalog, asset_id=asset_id)
            # offers = dataset.get('odrl:hasPolicy', [])
            # return offers

        if not r.status_code == 200:
            print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
            return None
        j = r.json()
        offers = j.get('odrl:hasPolicy', [])
        if not isinstance(offers, list):
            offers = [offers]
        return offers

    def get_catalog_edc_workaround(self, asset_id: str):
        """
        seems this filter works only on properties, so we assume, still (not mandatory field) asset:prop:id is used!
        """
        catalog = self.fetch_catalog(filter={
            #'offset': 0,
            #'limit': 1,
            'filterExpression' : {
                'operandLeft': 'https://w3id.org/edc/v0.0.1/ns/id',
                'operator': '=',
                'operandRight': asset_id
            }
        })
        return catalog

    def negotiation(self, dataset_id: str, offer: OdrlOffer, consumer_callback_base_url: str, provider_base_url: str):
        contract_request_id = str(uuid4())
        contract_request_message =  ContractRequestMessage(
            field_id=contract_request_id,
            dspace_process_id=contract_request_id, # TODO: this should not be required, but EDC needs it
            dspace_dataset=dataset_id,
            dspace_offer=offer,
            dspace_callback_address=consumer_callback_base_url,
        )
        data = contract_request_message.dict(exclude_unset=False)
        data['datasetId'] = dataset_id
        data['edc:assetId'] = dataset_id
        data['dspace:offer']['https://w3id.org/edc/v0.0.1/ns/assetId'] = dataset_id
        data['dspace:offer']['odrl:target'] = dataset_id # TODO: this is required by EDC, check with spec!
        offer_id = data.get('dspace:offer').get('@id')
        data['dspace:offer']['https://w3id.org/edc/v0.0.1/ns/offerId'] = offer_id # workaround for EDC

        # the next step uses an internal 'requests' call that is mocked with the @patch test case annotation
        result = self.post("/negotiations/request", data=data)
        return result

    def negotiation_callback_result(self, id: str, consumer_callback_base_url: str):
        r = requests.get(f"{consumer_callback_base_url}/negotiations/{id}/agreement")
        if not r.status_code == 200:
            print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
            return None
        j = r.json()
        return j

    def transfer(self, agreement_id_received: str, consumer_callback_base_url: str, provider_base_url: str):
        transfer_request_id = str(uuid4())
        transfer_request_message: TransferRequestMessage = TransferRequestMessage(
            field_id = transfer_request_id,
            dspace_agreement_id = agreement_id_received,
            dct_format = DCT_FORMAT_HTTP,
            dspace_callback_address = consumer_callback_base_url,
            dspace_data_address = 'HttpData'
        )
        data = transfer_request_message.dict(exclude_unset=False)
        data['dspace:processId'] = transfer_request_id # EDC requires this https://github.com/eclipse-edc/Connector/issues/3253
        data['dspace:dataAddress'] = {
                "https://w3id.org/edc/v0.0.1/ns/type":"HttpProxy"
        }
        #r = requests.post(f"{provider_base_url}/transfers/request", json=data)
        result = self.post(path="/transfers/request", data=data)
        return result

    def transfer_callback_result(self, id: str, consumer_callback_base_url: str):
        r = requests.get(f"{consumer_callback_base_url}/private/transfers/{id}")
        if not r.status_code == 200:
            print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
            return None
        j = r.json()
        return j

