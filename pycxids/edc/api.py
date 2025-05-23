# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
import json
from uuid import uuid4
from time import sleep
import requests
from pycxids.utils.api import GeneralApi

from pycxids.edc.settings import RECEIVER_SERVICE_BASE_URL
from pycxids.utils.jsonld import default_context

EDC_NAMESPACE = 'https://w3id.org/edc/v0.0.1/ns/'
EDC_ASSET_TYPE = EDC_NAMESPACE + 'AssetEntryDto'
EDC_DATA_ADDRESS_TYPE = EDC_NAMESPACE + "DataAddress"
EDC_SIMPLE_TYPE = EDC_NAMESPACE + 'type'
#EDC_ASSET_DATA_ADDRESS = EDC_NAMESPACE + 'dataAddress'
EDC_CATALOG_REQUEST_PROTOCOL = EDC_NAMESPACE + "protocol"

DATASPACE_PROTOCOL_HTTP = "dataspace-protocol-http"

ODRL_PREFIX = 'odrl'
ODRL_SCHEMA = 'http://www.w3.org/ns/odrl/2/'


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
            if data.get('state') == final_state or data.get('edc:state') == final_state: # before and after 0.4.0
                return data

            counter = counter+1
            if counter >= timeout:
                return None

            sleep(1)


class EdcProvider(EdcDataManagement):
    def __init__(self, edc_data_managment_base_url: str, auth_key: str) -> None:
        super().__init__(edc_data_managment_base_url, auth_key)

    def create_asset_and_friends(self,
            base_url: str,
            asset_id: str = '',
            proxyPath=False, proxyQueryParams=False, proxyBody=False, proxyMethod=False,
            asset_additional_props:dict={},
            data_address_additional_props:dict={},
        ):
        asset_id_created = self.create_asset(
            base_url=base_url,
            asset_id=asset_id,
            proxyPath=proxyPath,
            proxyQueryParams=proxyQueryParams,
            proxyBody=proxyBody,
            proxyMethod=proxyMethod,
            asset_additional_props=asset_additional_props,
            data_address_additional_props=data_address_additional_props,
        )
        if not asset_id_created:
            # TODO: better error handling
            return (None, None, None)
        policy_id = self.create_policy(asset_id=asset_id_created)
        contract_id = self.create_contract_definition(policy_id=policy_id, asset_id=asset_id_created)
        return(asset_id_created, policy_id, contract_id)

    def create_asset_s3(self, filename_in_bucket: str, bucket_name: str, asset_id: str = ''):
        """
        Creates an S3 asset
        """
        if not asset_id:
            asset_id = str(uuid4())
        data = {
            "@context": default_context,
            "@type": EDC_ASSET_TYPE,
            "@id": asset_id,
            "edc:asset": {
                "@id": asset_id,
                "properties": {
                    "asset:prop:id": asset_id,
                    "asset:prop:contenttype": "application/json",
                    "asset:prop:policy-id": "use-eu",
                }
            },
            "edc:dataAddress": {
                #"@type": EDC_DATA_ADDRESS_TYPE,
                "edc:type": "AmazonS3",
                "edc:bucketName": bucket_name,
                "edc:region": "eu-central-1",
                "edc:keyName": filename_in_bucket,
            }
        }
        result = self.post(path="/v3/assets", data=data, json_content=True)
        if result == None:
            return None
        created_id = result.get("@id")
        return created_id




    def create_asset(self,
            base_url: str,
            asset_id: str = '',
            proxyPath=False, proxyQueryParams=False, proxyBody=False, proxyMethod=False,
            try_delete_before_create=False,
            asset_additional_props:dict={},
            data_address_additional_props:dict={},
            data_address_type:str="HttpData",
        ):
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

        # default is data management V3 now
        # or overwrite below
        data = {
            "@context": default_context,
            "@type": EDC_ASSET_TYPE,
            "@id": asset_id,
            "edc:properties": {
                "asset:prop:id": asset_id,
                "asset:prop:contenttype": "application/json",
                "asset:prop:policy-id": "use-eu",
            },
            "edc:dataAddress": {
                #"@type": EDC_DATA_ADDRESS_TYPE,
                "edc:type": data_address_type,
                "edc:proxyPath": str(proxyPath).lower(),
                "edc:proxyQueryParams": str(proxyQueryParams).lower(),
                "edc:proxyMethod": str(proxyMethod).lower(),
                "edc:proxyBody": str(proxyBody).lower(),
                "edc:baseUrl": base_url,

            }
        }
        with open('asset_v2.json', 'w') as f:
            tmp = json.dumps(data, indent=4)
            f.write(tmp)

        for k,v in asset_additional_props.items():
            data['asset']['properties'][k] = v
        for k,v in data_address_additional_props.items():
            data['dataAddress']['properties'][k] = v
        # in V2, the response is json-ld. TODO: is the @id the message, or the asset:prop:id???
        result = self.post(path="/v3/assets", data=data, json_content=True)
        if result == None:
            return None
        created_id = result.get("@id")
        return created_id

    def create_policy(self, asset_id: str, odrl_constraint:dict = None, policy_id: str = None):
        """
        "odrl:constraint": {
            "@type": "LogicalConstraint",
            "odrl:and": [
                {
                    "@type": "Constraint",
                    "odrl:leftOperand": "PURPOSE",
                    "odrl:operator": {
                        "@id": "odrl:eq"
                    },
                    "odrl:rightOperand": "abc"
                },
                {
                    "@type": "Constraint",
                    "odrl:leftOperand": "PURPOSE",
                    "odrl:operator": {
                        "@id": "odrl:eq"
                    },
                    "odrl:rightOperand": "ID 3.1 Trace"
                }
            ]
        }
        """
        if not policy_id:
            policy_id = str(uuid4())
        data = {
            "@context": default_context,
            #"@type": "PolicyDefinitionRequestDto",
            "@id": policy_id,
            "edc:policy": {
                "@type": "odrl:Set", # TODO: 0.7.0 doesn't allow 'Policy' but MUST be 'Set'
                "odrl:target": asset_id,
                "odrl:permission": [ # TODO: permission or permissionS
                    {
                        "odrl:action": "use",
                    }
                ],
            },
        }
        # if a constraint is given, add it to the policy
        if odrl_constraint:
            data['edc:policy']['odrl:permission'][0]['odrl:constraint'] = odrl_constraint
        with open('policy_debug.json', 'wt') as f:
            f.write(json.dumps(data, indent=True))
        result = self.post(path="/v2/policydefinitions", data=data, json_content=False)
        if result == None:
            return None
        return policy_id

    def create_access_policy(self, bpn: str = None):
        policy_id = str(uuid4())
        data = {
            "@context": default_context,
            #"@type": "PolicyDefinitionRequestDto",
            "@id": policy_id,
            "edc:policy": {
                "@type": "odrl:Set", # TODO: EDC 0.7.0 it MUST be 'Set' and 'Policy' is not allowed.
                #"odrl:permission": [],
            },
        }
        if bpn:
            permission = {
                "odrl:action": "use",
                "odrl:constraint": {
                    #"@type": "LogicalConstraint",
                    "@type": "Constraint",
                    "odrl:leftOperand": "BusinessPartnerNumber",
                    "odrl:operator": {
                        "@id": "odrl:eq"
                    },
                    "odrl:rightOperand": bpn
                }
            }
            data['edc:policy']['odrl:permission'] = permission

        result = self.post(path="/v2/policydefinitions", data=data, json_content=False)
        if result == None:
            return None
        return policy_id


    def create_contract_definition(self, policy_id: str, asset_id: str, access_policy_id = None):
        if not access_policy_id:
            access_policy_id = self.create_access_policy()
        cd_id = str(uuid4())
        data = {
            "@context": default_context,
            #"@type": "ContractDefinition",
            "@id": cd_id,
            "edc:accessPolicyId": access_policy_id,
            "edc:contractPolicyId": policy_id,
            "edc:assetsSelector": [ # wrong key here, leads to applying it to all assets?
                {
                    "edc:operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
                    #"operandLeft": "edc:id", # TODO: not sure why this doesn't work
                    "edc:operator": "=", # TODO: 'eq' here, kills the catalog ;-)
                    "edc:operandRight": asset_id
                }
            ],
        }

        result = self.post(path="/v2/contractdefinitions", data=data, json_content=False)
        if result == None:
            return None
        return cd_id

    def get_number_of_elements(self, path: str, limit = 1000000):
        """
        Returns the number of elements for a requested path, e.g. assets, policydefinitions, contractdefinitions
        """
        try:
            if not path.endswith('/request'):
                path = path + '/request'
            data = {

            }
            data['@context'] = default_context
            j = self.post(path=path, data=None)
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
        dataset_match = None
        for dataset in catalog['dcat:dataset']:
            id = dataset.get('@id')
            if id == asset_id:
                dataset_match = dataset
                break
            edc_id = dataset.get('edc:id')
            if edc_id == asset_id:
                dataset_match = dataset
                break
        if not dataset_match:
            return None
        # now the offers, just get the first
        offers = dataset_match.get('odrl:hasPolicy')
        if not offers:
            return None
        if not isinstance(offers, list):
            offers = [offers]

        # just return the first
        return offers[0]


    def get_dataset(self, dataset_id: str, provider_ids_endpoint: str):
        """
        dataset_id == asset_id
        Use a filter to only get results for a given asset  / dataset id
        """
        data = {
            "@context": {
                "dspace": "https://w3id.org/dspace/v0.8/",
            },
            "protocol": DATASPACE_PROTOCOL_HTTP, # TODO: what is this actually used for?
            'providerUrl': provider_ids_endpoint,
            'querySpec': {
                "filterExpression": {
                    "operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
                    #"operandLeft": "https://w3id.org/edc/v0.0.1/ns/asset:porp:id",
                    "operator": "=",
                    "operandRight": dataset_id,
                }
            }
        }
        with open('catalog_request_dataset.json', 'w') as f:
            f.write(json.dumps(data, indent=4))
        catalog = self.post(path='/v2/catalog/request', data=data)
        # sorry, but this is stupid, if only 1 item in the database, it is NOT a list, otherwise it is
        # this was not the intension of the Dspace protocol!
        # making this always a list here for now
        if not isinstance(catalog['dcat:dataset'], list):
            catalog['dcat:dataset'] = [catalog['dcat:dataset']]

        return catalog


    def get_catalog(self, provider_ids_endpoint, provider_participant_id: str):
        """
        Fetch the catalog from a data provider

        provider_participant_id: BPN of the Provider
        """
        data = {
            "@context": default_context,
            "edc:protocol": DATASPACE_PROTOCOL_HTTP, # TODO: what is this actually used for?
            #'providerUrl': provider_ids_endpoint,
            'edc:counterPartyAddress': provider_ids_endpoint,
            'edc:counterPartyId': provider_participant_id,
        }
        with open('catalog_request_new.json', 'w') as f:
            f.write(json.dumps(data, indent=4))
        catalog = self.post(path='/v2/catalog/request', data=data)
        # sorry, but this is stupid, if only 1 item in the database, it is NOT a list, otherwise it is
        # this was not the intension of the Dspace protocol!
        # making this always a list here for now
        if not isinstance(catalog['dcat:dataset'], list):
            catalog['dcat:dataset'] = [catalog['dcat:dataset']]

        return catalog

    def negotiate_contract_and_wait(self, provider_ids_endpoint, contract_offer, asset_id: str,
                                    provider_participant_id: str,
                                    consumer_participant_id: str,
                                    timeout = 30):
        """
        Because of some EDC reasons we need the provider_participant_id on the consumer side.
        It will be mapped later against the provider sent agreement and if not used here on consumer side,
        it will produce a very mis-leading error: "Invalid client credentials: Invalid counter-party identity"
        Result: The negotiated contract (contains the agreementId)
        """
        offer_id = contract_offer.get('@id')
        assert offer_id, "Could not find @id in contract_offer"

        offer = deepcopy(contract_offer)
        offer["odrl:assigner"] = { "@id": provider_participant_id }

        data = {
            "@context": default_context,
            "@type": "NegotiationInitiateRequestDto",
            "edc:counterPartyAddress": provider_ids_endpoint,
            "edc:protocol": "dataspace-protocol-http",
            "edc:policy": offer,
        }
        with open('contractnegotiation_request_to_edc.json', 'wt') as f:
            mystr = json.dumps(data, indent=4)
            f.write(mystr)
        result = self.post(path="/v2/contractnegotiations", data=data)
        negotiation_id = result.get('@id')
        negotiation_data = self.wait_for_state(path=f"/v2/contractnegotiations/{negotiation_id}", final_state='FINALIZED', timeout=timeout)
        return negotiation_data

    def transfer(self, provider_ids_endpoint: str, asset_id: str, agreement_id: str,
                    provider_participant_id: str = 'BPNLprovider',
                    consumer_participant_id: str = 'BPNLconsumer'):

        """
        Probably we don't need to wait for the state to change, because we'll receive  the EDR token when everything is ok
        """
        receiver_service_base_url = self.token_receiver_service_base_url
        if not receiver_service_base_url:
            receiver_service_base_url = RECEIVER_SERVICE_BASE_URL
            print("token_receiver_service_base_url not given, using default from settings: {receiver_service_base_url}")
        transfer_request = {
            "@context": default_context,
            "@type": "edc:TransferRequest",
            "edc:assetId": asset_id,
            "edc:counterPartyAddress": provider_ids_endpoint,
            "edc:contractId": agreement_id,

            "edc:dataDestination": {
                "edc:type": "HttpProxy"
            },
            "edc:protocol": "dataspace-protocol-http",
            "edc:transferType": "HttpData-PULL",
            "edc:callbackAddresses": [
                {
                    "edc:transactional": False,
                    "edc:uri": f"{receiver_service_base_url}/datareference",
                    "edc:events": [
                        "transfer.process"
                    ]
                }
            ]
        }
        data = self.post("/v2/transferprocesses", data=transfer_request)
        return data['@id']

    def edr_start_process(self, provider_ids_endpoint, contract_offer, timeout = 30, asset_id: str = None,
                                    provider_participant_id: str = 'BPNLprovider',
                                    consumer_participant_id: str = 'BPNLconsumer'):
        """
        https://github.com/eclipse-tractusx/tractusx-edc/blob/main/docs/samples/edr-api-overview/edr-api-overview.md#edr-negotiation--contract-negotiation-and-transfer-process-in-a-single-request
        https://app.swaggerhub.com/apis/eclipse-tractusx-bot/tractusx-edc/0.5.1#/Control%20Plane%20EDR%20Api/initiateEdrNegotiation
        """
        base_url_without_v2 = self.base_url.replace('/v2', '')
        offer_id = contract_offer.get('@id')
        data = {
            "@context": {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
                "odrl": "http://www.w3.org/ns/odrl/2/"
            },
            "@type": "NegotiationInitiateRequestDto",
            "connectorAddress": provider_ids_endpoint,
            "protocol": "dataspace-protocol-http",
            "connectorId": provider_participant_id, # TODO
            "providerId": provider_participant_id, # TODO
            #"consumerId": consumer_participant_id, # TODO
            "offer": {
                "offerId": offer_id,
                "assetId": asset_id,
                "policy": contract_offer,
            }

        }
        r = requests.post(f"{base_url_without_v2}/edrs", json=data, headers=self.headers)
        result = r.json()
        return result

    def edr_tp(self, transfer_id: str):
        base_url_without_v2 = self.base_url.replace('/v2', '')
        r = requests.get(f"{base_url_without_v2}/edrs/{transfer_id}", headers=self.headers)
        result = r.json()
        return result

    def edr_for_negotiation(self, negotiation_id: str, timeout = 30):
        """
        Right now (0.5.1) the EDR api does not provide a way to identify the EDR for the initiated contract negotiation.
        Thus, we need to do that manually for now.

        Waits for timout seconds or state to be FINALIZED
        """
        agreement_id = self.agreement_for_negotiation(negotiation_id=negotiation_id, timeout=timeout)
        edr_token = self.edr_token(agreement_id=agreement_id)
        return edr_token

    def agreement_for_negotiation(self, negotiation_id: str, timeout = 30):
        """
        Translates (and waits) from a negotiation_id to the agreement_id (once available).
        Return: agreement_id
        """
        negotiation_data = self.wait_for_state(path=f"/contractnegotiations/{negotiation_id}", final_state='FINALIZED', timeout=timeout)
        agreement_id = negotiation_data.get('edc:contractAgreementId')
        return agreement_id

    def edr_token(self, agreement_id = None, asset_id = None, timeout: int = 30):
        base_url_without_v2 = self.base_url.replace('/v2', '')
        params = {}
        if agreement_id:
            params['agreementId'] = agreement_id
        if asset_id:
            params['assetId'] = asset_id

        transfers = None
        # workaround
        counter = 0
        while True:
            r = requests.get(f"{base_url_without_v2}/edrs", headers=self.headers, params=params)
            result = r.json() # TODO: probably needs to be filtered for tx:edrState': 'NEGOTIATED'
            if len(result):
                transfers = result
                break

            counter = counter+1
            if counter >= timeout:
                return None
            sleep(1)


        if not transfers:
            print(f"No transfers for asset_id: {asset_id} agreement_id: {agreement_id}")
            return None
        tp_id = transfers[0].get('edc:transferProcessId') # TODO: assuming ther can be only 1 valid element
        edr = self.edr_tp(transfer_id=tp_id)
        return edr

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

    def negotiate_and_transfer(self, provider_ids_endpoint: str, asset_id: str,
                               provider_participant_id: str,
                               consumer_participant_id: str) -> str:
        """
        Returns the transer_id
        """
        catalog = self.get_catalog(provider_ids_endpoint=provider_ids_endpoint)
        contract_offer = self.find_first_in_catalog(catalog=catalog, asset_id=asset_id)
        negotiated_contract = self.negotiate_contract_and_wait(provider_ids_endpoint=provider_ids_endpoint,
            contract_offer=contract_offer, asset_id=asset_id, provider_participant_id=provider_participant_id,
            consumer_participant_id=consumer_participant_id)
        agreement_id = negotiated_contract.get('edc:contractAgreementId', '')
        print(f"agreementId: {agreement_id}")

        transfer_id = self.transfer(provider_ids_endpoint=provider_ids_endpoint,
            asset_id=asset_id, agreement_id=agreement_id, provider_participant_id=provider_participant_id, consumer_participant_id=consumer_participant_id)
        return agreement_id, transfer_id
