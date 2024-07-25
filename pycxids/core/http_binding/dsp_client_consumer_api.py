#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import sys
from typing import List
from pycxids.cli.cli_settings import *
import requests
from uuid import uuid4
from pycxids.core.auth.auth_factory import AuthFactory
from pycxids.utils.helper import print_red
from pycxids.core.daps import Daps
from pycxids.core.http_binding.settings import DCT_FORMAT_HTTP

from pycxids.core.http_binding.models import CatalogOffer, ContractAgreementMessage, ContractNegotiation, ContractRequestMessage, DataAddress, EndpointProperties, EndpointPropertyNames, OdrlOffer, TransferProcess, TransferRequestMessage, TransferStartMessage
from pycxids.utils.api import GeneralApi
from pycxids.utils.jsonld import DEFAULT_DSP_REMOTE_CONTEXT, compact

class DspClientConsumerApi(GeneralApi):
    def __init__(self, provider_base_url: str, auth: AuthFactory, bearer_scopes: list = None, provider_did: str = None) -> None:
        super().__init__(base_url=provider_base_url)
        self.auth = auth
        self.bearer_scopes = bearer_scopes
        self.provider_did = provider_did

        self.headers = {}
        self._update_auth_token()

    def _update_auth_token(self):
        opts = {}
        if self.bearer_scopes:
            opts['bearer_scopes'] = self.bearer_scopes
        if self.provider_did:
            opts['provider_did'] = self.provider_did
        token = self.auth.get_token(aud=self.base_url, opts=opts) # audience is always only the base_url
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
        if not j:
            return None
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
    
    def get_offers_for_dataset(self, dataset_id: str) -> List[CatalogOffer]:
        """
        Uses typed offers instead of dicts, but uses existing method to fetch the dict.
        """
        offers_dict = self.get_offers_for_asset(asset_id=dataset_id)
        offers = []
        for o in offers_dict:
            offer = CatalogOffer.parse_obj(o)
            offers.append(offer)
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

    def negotiation(self, dataset_id: str, offer: CatalogOffer, consumer_callback_base_url: str) -> ContractNegotiation:
        contract_request_id = str(uuid4())
        consumer_pid = str(uuid4())
        # in the catalog offer there is no odrl:target included, in the request, it is required
        offer_with_target = OdrlOffer.parse_obj(offer)
        offer_with_target.odrl_target = dataset_id
        contract_request_message =  ContractRequestMessage(
            field_id=contract_request_id,
            dspace_consumer_pid=consumer_pid,
            dspace_dataset=dataset_id,
            dspace_offer=offer_with_target,
            dspace_callback_address=consumer_callback_base_url
        )
        data = contract_request_message.dict(exclude_unset=False)

        # debugging
        # with open('tmp_consumer_request_msg.json', 'wt') as f:
        #     f.write(json.dumps(data, indent=True))

        self._update_auth_token()
        result = self.post("/negotiations/request", data=data)
        result_c = compact(doc=result, context=DEFAULT_DSP_REMOTE_CONTEXT)
        cn = ContractNegotiation.parse_obj(result_c)
        return cn

    def negotiation_callback_result(self, id: str, consumer_callback_base_url: str) -> ContractAgreementMessage:
        r = requests.get(f"{consumer_callback_base_url}/negotiations/{id}/agreement")
        if not r.status_code == 200:
            print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
            return None
        j = r.json()
        j_c = compact(doc=j, context=DEFAULT_DSP_REMOTE_CONTEXT)
        agreement_message = ContractAgreementMessage.parse_obj(j)
        return agreement_message

    def transfer(self, agreement_id_received: str, consumer_pid: str, consumer_callback_base_url: str) -> TransferProcess:
        transfer_request_id = str(uuid4())
        consumer_pid = str(uuid4())
        transfer_request_message: TransferRequestMessage = TransferRequestMessage(
            field_id = transfer_request_id,
            dspace_consumer_pid = consumer_pid,
            dspace_agreement_id = agreement_id_received,
            dct_format = DCT_FORMAT_HTTP,
            dspace_callback_address = consumer_callback_base_url
        )
        data = transfer_request_message.dict(exclude_unset=False)


        # with open('transfer_request_message_dsp.json', 'wt') as f:
        #     f.write(json.dumps(data, indent=True))
        self._update_auth_token()
        result = self.post(path="/transfers/request", data=data)
        result_c = compact(doc=result, context=DEFAULT_DSP_REMOTE_CONTEXT)
        tp = TransferProcess.parse_obj(result_c)
        return tp

    def transfer_callback_result(self, id: str, consumer_callback_base_url: str) -> TransferStartMessage:
        r = requests.get(f"{consumer_callback_base_url}/private/transfers/{id}")
        if not r.status_code == 200:
            print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
            return None
        j = r.json()
        j_c = compact(doc=j, context=DEFAULT_DSP_REMOTE_CONTEXT)
        transfer_start_message = TransferStartMessage.parse_obj(j_c)
        return transfer_start_message

    @classmethod
    def get_data_address_property(cls, data_address:DataAddress, name: str):
        value = None
        prop:EndpointProperties = None
        for prop in data_address.dspace_endpoint_properties:
            if prop.dspace_name == name:
                value = prop.dspace_value
                break
        return value

    @classmethod
    def get_data_address_authorization(cls, data_address:DataAddress):
        """
        Simple helper for get_data_address_property()
        """
        return cls.get_data_address_property(data_address=data_address, name=EndpointPropertyNames.https___w3id_org_edc_v0_0_1_ns_authorization)

    @classmethod
    def get_data_address_endpoint(cls, data_address:DataAddress):
        """
        Simple helper for get_data_address_property()
        """
        return cls.get_data_address_property(data_address=data_address, name=EndpointPropertyNames.https___w3id_org_edc_v0_0_1_ns_endpoint)
