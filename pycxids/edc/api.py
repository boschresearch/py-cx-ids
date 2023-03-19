# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4
from time import sleep
import requests
from pycxids.utils.api import GeneralApi

class TokenReceiverServiceNotGiven(Exception):
    pass


class EdcDataManagement(GeneralApi):
    def __init__(self, edc_data_managment_base_url: str, auth_key: str) -> None:
        super().__init__(base_url=edc_data_managment_base_url, headers={'X-Api-Key': auth_key})

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


class EdcProvider(EdcDataManagement):
    def __init__(self, edc_data_managment_base_url: str, auth_key: str) -> None:
        super().__init__(edc_data_managment_base_url, auth_key)

    def create_asset_and_friends(self, base_url: str, asset_id: str = '', proxyPath=False, proxyQueryParams=False, proxyBody=False, proxyMethod=False, data_address_additional_props:dict={}):
        asset_id = self.create_asset(
            base_url=base_url,
            asset_id=asset_id,
            proxyPath=proxyPath,
            proxyQueryParams=proxyQueryParams,
            proxyBody=proxyBody,
            proxyMethod=proxyMethod,
            data_address_additional_props=data_address_additional_props,
        )
        policy_id = self.create_policy(asset_id=asset_id)
        contract_id = self.create_contract_definition(policy_id=policy_id, asset_id=asset_id)
        return(asset_id, policy_id, contract_id)

    def create_asset(self, base_url: str, asset_id: str = '', proxyPath=False, proxyQueryParams=False, proxyBody=False, proxyMethod=False, try_delete_before_create=False, data_address_additional_props:dict={}):
        if not asset_id:
            asset_id = str(uuid4())
        else:
            if try_delete_before_create:
                # this makes only sense if asset_id was given
                pass
                # disable for now, since after an negotiated contract,
                # the asset can NOT be deleted anymore.
                # optional: delete the contract definition to not let it appear in the catalog anymore
                #r = self.delete(path=f"/assets/{asset_id}")
                # just try and do nothing else here

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
        for k,v in data_address_additional_props.items():
            data['dataAddress']['properties'][k] = v
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

    def get_number_of_elements(self, path: str, limit = 1000000):
        """
        Returns the number of elements for a requested path, e.g. assets, policydefinitions, contractdefinitions
        """
        try:
            j = self.get(path=path, params={ 'limit': limit })
            return len(j)
        except Exception as ex:
            print(ex)

        return None




class EdcConsumer(EdcDataManagement):
    """
    Process description:
    https://github.com/catenax-ng/product-edc/blob/0.1.1/docs/data-transfer/Transfer%20Data.md

    token_receiver_service_base_url: pycxids.edc.token_receiver_service that is used with EDC_RECEIVER_HTTP_ENDPOINT
        where the EDC sends its received token to.
    """

    def __init__(self, edc_data_managment_base_url: str, auth_key: str, token_receiver_service_base_url: str = None) -> None:
        super().__init__(edc_data_managment_base_url=edc_data_managment_base_url, auth_key=auth_key)
        self.token_receiver_service_base_url = token_receiver_service_base_url

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

    def negotiate_contract_and_wait_with_asset(self, provider_ids_endpoint: str, asset_id: str, timeout = 30):
        """
        Negotiate a contract / an agreement for the given asset.
        It uses the first (!) avialable policy - beware, that this is not suitable for production ready systems!
        Returns the agreement_id
        """
        catalog = self.get_catalog(provider_ids_endpoint=provider_ids_endpoint)
        contract_offer = self.find_first_in_catalog(catalog=catalog, asset_id=asset_id)
        negotiated_contract = self.negotiate_contract_and_wait(provider_ids_endpoint=provider_ids_endpoint, contract_offer=contract_offer, timeout=timeout)
        agreement_id = negotiated_contract.get('contractAgreementId', None)
        return agreement_id

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

    def transfer_and_wait_consumer_edr(self, provider_ids_endpoint: str, asset_id: str, agreement_id: str, timeout = 30):
        """
        Fetches the EDR token from the token_receiver_service.

        """
        if not self.token_receiver_service_base_url:
            raise TokenReceiverServiceNotGiven()
        transfer_id = self.transfer(provider_ids_endpoint=provider_ids_endpoint, asset_id=asset_id, agreement_id=agreement_id)
        return self._transfer_and_wait_url(token_receiver_service_url=f"{self.token_receiver_service_base_url}/{transfer_id}/token/consumer", timeout=timeout)

    def transfer_and_wait_provider_edr(self, provider_ids_endpoint: str, asset_id: str, agreement_id: str, timeout = 30):
        """
        Fetches the EDR token from the token_receiver_service.

        """
        if not self.token_receiver_service_base_url:
            raise TokenReceiverServiceNotGiven()
        transfer_id = self.transfer(provider_ids_endpoint=provider_ids_endpoint, asset_id=asset_id, agreement_id=agreement_id)
        return self._transfer_and_wait_url(token_receiver_service_url=f"{self.token_receiver_service_base_url}/{transfer_id}/token/provider", timeout=timeout)

    def edr_provider_wait(self, transfer_id: str, timeout = 30):
        if not self.token_receiver_service_base_url:
            raise TokenReceiverServiceNotGiven()
        return self._transfer_and_wait_url(token_receiver_service_url=f"{self.token_receiver_service_base_url}/{transfer_id}/token/provider", timeout=timeout)

    def edr_consumer_wait(self, transfer_id: str, timeout = 30):
        if not self.token_receiver_service_base_url:
            raise TokenReceiverServiceNotGiven()
        return self._transfer_and_wait_url(token_receiver_service_url=f"{self.token_receiver_service_base_url}/{transfer_id}/token/consumer", timeout=timeout)

    def _transfer_and_wait_url(self, token_receiver_service_url: str, timeout = 30):
        params = {
            'timeout' : timeout,
        }
        r = requests.get(token_receiver_service_url, params=params) # no authentication at the service required

        if not r.ok:
            print(f"{r.status_code} - {r.reason} - {r.content}")
            return None

        j = r.json()
        return j

    def negotiate_and_transfer(self, provider_ids_endpoint: str, asset_id: str) -> str:
        """
        Returns the transer_id
        """
        catalog = self.get_catalog(provider_ids_endpoint=provider_ids_endpoint)
        contract_offer = self.find_first_in_catalog(catalog=catalog, asset_id=asset_id)
        negotiated_contract = self.negotiate_contract_and_wait(provider_ids_endpoint=provider_ids_endpoint,
            contract_offer=contract_offer)
        negotiated_contract_id = negotiated_contract.get('id', '')
        agreement_id = negotiated_contract.get('contractAgreementId', '')
        print(f"agreementId: {agreement_id}")

        transfer_id = self.transfer(provider_ids_endpoint=provider_ids_endpoint,
            asset_id=asset_id, agreement_id=agreement_id)
        return agreement_id, transfer_id
