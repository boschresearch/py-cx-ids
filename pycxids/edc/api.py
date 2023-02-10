# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4
from time import sleep
import requests

class EdcDataManagement():
    def __init__(self, edc_data_managment_base_url: str, auth_key: str) -> None:
        self.base_url = edc_data_managment_base_url
        self.auth_key = auth_key

    def get(self, path: str, params = None):
        """
        Generic EDC API GET request
        """
        r = requests.get(f"{self.base_url}{path}", params=params, headers=self._prepare_auth_header())

        if not r.ok:
            print(f"{r.status_code} - {r.reason} - {r.content}")
            return None
        
        j = r.json()
        return j
    
    def post(self, path: str, data = None, json_content = True):
        """
        Generic EDC API POST request
        """
        r = requests.post(f"{self.base_url}{path}", json=data, headers=self._prepare_auth_header())

        if not r.ok:
            print(f"{r.status_code} - {r.reason} - {r.content}")
            return None
        
        if not json_content:
            return r.content
        j = r.json()
        return j

    def wait_for_state(self, path: str, final_state: str, timeout = 30):
        """
        Fetches the given endpoint until final_state is reached - or timeout
        """
        counter = 0
        while True:
            data = self.get(path=path)
            if data['state'] == final_state:
                return data

            counter = counter+1
            if counter >= timeout:
                return None

            sleep(1)

    def _prepare_auth_header(self):
        return {
            'X-Api-Key': self.auth_key
        }

class EdcProvider(EdcDataManagement):
    def __init__(self, edc_data_managment_base_url: str, auth_key: str) -> None:
        super().__init__(edc_data_managment_base_url, auth_key)

    def create_asset(self, base_url: str, asset_id: str = '', proxyPath=False, proxyQueryParams=False, proxyBody=False, proxyMethod=False):
        if not asset_id:
            asset_id = str(uuid4())

        data = {
            "asset": {
                "properties": {
                    "asset:prop:id": asset_id,
                    "asset:prop:contenttype": "application/json",
                    "asset:prop:policy-id": "use-eu",
                }
            },
            "dataAddress": {
                "properties": {
                    "type": "HttpData",
                    "proxyPath": proxyPath,
                    "proxyQueryParams": proxyQueryParams,
                    "proxyMethod": proxyMethod,
                    "proxyBody": proxyBody,
                    "baseUrl": base_url,
                }
            }
        }
        result = self.post(path="/assets", data=data, json_content=False)
        if result == None:
            return None
        return asset_id

    def create_policy(self, asset_id: str):
        policy_id = str(uuid4())
        data = {
            "id": policy_id,
            "policy": {
                "permissions": [
                    {
                        "target": asset_id,
                        "action": {
                            "type": "USE"
                        },
                        "edctype": "dataspaceconnector:permission"
                    }
                ],
            },
            "@type": {
                "@policytype": "set"
            }
        }
        result = self.post(path="/policydefinitions", data=data, json_content=False)
        if result == None:
            return None
        return policy_id

    def create_contract_definition(self, policy_id: str, asset_id: str):
        cd_id = str(uuid4())
        data = {
            "id": cd_id,
            "accessPolicyId": policy_id,
            "contractPolicyId": policy_id,
            "criteria": [
                {
                    "operandLeft": "asset:prop:id",
                    "operator": "=",
                    "operandRight": asset_id
                }
            ],
        }
        result = self.post(path="/contractdefinitions", data=data, json_content=False)
        if result == None:
            return None
        return cd_id



class EdcConsumer(EdcDataManagement):
    """
    Process description:
    https://github.com/catenax-ng/product-edc/blob/0.1.1/docs/data-transfer/Transfer%20Data.md    
    """

    def __init__(self, edc_data_managment_base_url: str, auth_key: str) -> None:
        super().__init__(edc_data_managment_base_url=edc_data_managment_base_url, auth_key=auth_key)

    @staticmethod
    def catalog_contract_offer_into_negotiation_contract_offer(catalog_contract_offer, connector_address: str):
        """
        TODO: check where this code should go to...
        """
        out_data = {
            'connectorId': 'foo', # TODO
            'offer': {}
        }
        out_data['connectorAddress'] = connector_address
        out_data['offer']['policy'] = catalog_contract_offer['policy']
        out_data['offer']['offerId'] = catalog_contract_offer['id']
        out_data['offer']['assetId'] = catalog_contract_offer['asset']['id']
        return out_data

    @staticmethod
    def find_first_in_catalog(catalog, asset_id:str):
        """
        Find a contract offer in the catalog the matches the asset_id
        TODO: check where this code should go to...
        TODO: We do NOT check which policy it contains!
        """
        for offer in catalog['contractOffers']:
            if offer['policy']['target'] == asset_id: # what are the arrays here?
                return offer
        return None

    def get_catalog(self, provider_ids_endpoint):
        """
        Fetch the catalog from a data provider
        """
        params = {
            'providerUrl': provider_ids_endpoint,
            'limit': 1000000,
        }
        catalog = self.get(path="/catalog", params=params)
        return catalog

    def negotiate_contract_and_wait(self, provider_ids_endpoint, contract_offer, timeout = 30):
        """
        Result: The negotiated contract (contains the agreementId)
        """
        negotiation_contract_offer = EdcConsumer.catalog_contract_offer_into_negotiation_contract_offer(catalog_contract_offer=contract_offer, connector_address=provider_ids_endpoint)
        data = self.post(path="/contractnegotiations", data=negotiation_contract_offer)
        negotiation_data = self.wait_for_state(path=f"/contractnegotiations/{data['id']}", final_state='CONFIRMED')
        return negotiation_data

    def transfer(self, provider_ids_endpoint: str, asset_id: str, agreement_id: str):
        """
        Probably we don't need to wait for the state to change, because we'll receive  the EDR token when everything is ok
        """
        transfer_request = {
            'id': str(uuid4()),
            'connectorId': 'foo', # TODO:
            'connectorAddress': provider_ids_endpoint,
            'contractId': agreement_id,
            'assetId': asset_id,
            'managedResource': False,
            'dataDestination': {
                'type': 'HttpProxy'
            }
        }
        data = self.post("/transferprocess", data=transfer_request)
        return data['id']
