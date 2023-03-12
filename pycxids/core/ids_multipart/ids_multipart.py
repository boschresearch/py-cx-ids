# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
import json
from threading import Thread
import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from datetime import datetime
import base64
import sys
from string import Template
import requests
from requests.auth import HTTPBasicAuth
from uuid import uuid4
from email import message_from_bytes, message_from_string
from requests_toolbelt.multipart import decoder
import uvicorn

from pycxids.core.ids import IdsBase
from pycxids.core import jwt_decode
from pycxids.core.ids_multipart import message_templates
from pycxids.core.ids_multipart.multipart_helper import IdsMultipartBase
from pycxids.core.settings import ASSERTION_TYPE, CERT_FN, CLIENT_ID, CONSUMER_CONNECTOR_URL, CONSUMER_CONNECTOR_URN, CONSUMER_WEBHOOK, DAPS_ENDPOINT, SCOPE, settings, endpoint_check
from pycxids.core.daps import get_daps_token
from pycxids.core.ids_multipart.webhook_queue import wait_for_message


class IdsMultipartConsumer(IdsMultipartBase):
    """
    A IDS Multipart consumer that is able to communicate with a fixed, given Provider
    """
    def __init__(self, private_key_fn: str, provider_connector_ids_endpoint: str,
            consumer_connector_urn=CONSUMER_CONNECTOR_URN, consumer_connector_webhook_url=CONSUMER_WEBHOOK,
            consumer_webhook_message_base_url = None,
            consumer_webhook_message_username = '',
            consumer_webhook_message_password = '',
            debug_messages=False, debug_out_dir=''
        ) -> None:
        super().__init__(
            consumer_connector_urn=consumer_connector_urn,
            consumer_connector_webhook_url=consumer_connector_webhook_url,
            debug_messages=debug_messages,
            debug_out_dir=debug_out_dir
        )
        self.private_key_fn = private_key_fn
        provider_connector_ids_endpoint = endpoint_check(provider_connector_ids_endpoint) # TODO: find a better solution
        self.connector_ids_endpoint = provider_connector_ids_endpoint
        self.debug_messages = debug_messages
        self.consumer_webhook_message_base_url = consumer_webhook_message_base_url
        self.consumer_webhook_message_username = consumer_webhook_message_username
        self.consumer_webhook_message_password = consumer_webhook_message_password

    def _get_daps_token(self):
        """
        Only for class internal use to get a dpas token.
        """
        return get_daps_token(audience=self.connector_ids_endpoint)

    def get_catalog(self, paging_from: int = 0, paging_to: int = 0):
        """
        Return the entire catalog or given pages of it

        # this is the EDC implementation to do paging - not standardized!
        if paging_from != 0 and paging_to != 0:
            header = json.loads(header_msg)
            header['from'] = paging_from
            header['to'] = paging_to
            header_msg = json.dumps(header)
        """
        daps_token = self._get_daps_token()
        header_msg = self.prepare_default_header(msg_type='ids:DescriptionRequestMessage', daps_access_token=daps_token['access_token'], provider_connector_ids_endpoint=self.connector_ids_endpoint)


        if self.debug_messages:
            self._debug_message(msg=header_msg, fn='request.json')

        header_received, payload_received = self._send_message(header_msg=header_msg, provider_connector_ids_endpoint=self.connector_ids_endpoint)
        return payload_received

    @classmethod
    def get_asset_ids_from_catalog(cls, catalog: dict):
        """
        Find all asset_ids in a given catalog
        """
        assets = set() # no double entries of assets
        for offer in catalog.get('ids:resourceCatalog', [])[0].get('ids:offeredResource', []):
            asset_prop_id = offer['ids:contractOffer'][0]['edc:policy:target']
            assets.add(asset_prop_id)
        return assets

    def get_offers(self, asset_id: str):
        """
        Return the offers for a given asset_id.
        Use filtering of the catalog endpoint.

        # this is IDS protocol to limit the result - which is not yet working in EDC
        # https://github.com/International-Data-Spaces-Association/IDS-G/blob/main/Communication/Message-Types/README.md#idsdescriptionrequestmessage
        if resource_uri:
            catalog_req_msg['ids:requestedElement'] = resource_uri

        # this is an IDS feature that seems not being supported in EDC
        header = json.loads(header_msg)
        header['ids:requestedElement'] = 'urn:uuid:028aaea9-ac01-4838-a516-00ef604ef128-urn:uuid:1b0a70a0-f64b-4c45-a808-4d35d3912fe5'
        header_msg = json.dumps(header)
        """
        catalog = self.get_catalog()
        # find contract offer for asset_id
        contract_offers = []
        for offer in catalog['ids:resourceCatalog'][0]['ids:offeredResource']: # could it be more than 1 item in the list?
            if offer['ids:contractOffer'][0]['edc:policy:target'] == asset_id: # what are the arrays here?
                contract_offers.append(offer)
        return contract_offers

    def negotiate(self, contract_offer: dict):
        """
        Returns the agreement_id
        """
        daps_token = self._get_daps_token()
        access_token = daps_token['access_token']
        transfer_contract_id = str(uuid4())
        header_msg = self.prepare_default_header(msg_type='ids:ContractRequestMessage', daps_access_token=access_token, provider_connector_ids_endpoint=self.connector_ids_endpoint, transfer_contract_id=transfer_contract_id)

        contract_request = {
            '@type': 'ids:ContractRequest',
            '@id': contract_offer['ids:contractOffer'][0]['@id'],
            'ids:permission':  contract_offer['ids:contractOffer'][0]['ids:permission'],
            'ids:provider': contract_offer['ids:contractOffer'][0]['ids:provider'],
            'ids:consumer': contract_offer['ids:contractOffer'][0]['ids:consumer'],
        }

        payload = json.dumps(contract_request)
        #print(json.dumps(contract_request, indent=4))
        header_received, payload_received = self._send_message(header_msg=header_msg, payload=payload, provider_connector_ids_endpoint=self.connector_ids_endpoint)

        correlation_id = transfer_contract_id
        agreement_header, agreement_payload = self.wait_for_message(key=correlation_id)
        #return agreement_header, agreement_payload
        agreement_id = agreement_payload.get('@id', None)
        return agreement_id

    def wait_for_message(self, key: str, timeout = 30):
        """
        Allows both options, fetch from the webhook server or transfer via thread
        """
        if self.consumer_webhook_message_base_url:
            params = {
                'timeout': timeout
            }
            r = requests.get(f"{self.consumer_webhook_message_base_url}/{key}", params=params, auth=HTTPBasicAuth(username=self.consumer_webhook_message_username, password=self.consumer_webhook_message_password))
            if not r.ok:
                print(f"{r.status_code} - {r.reason} - {r.content}")
                return None
            j = r.json()
            header = j.get('header')
            payload = j.get('payload')
            return header, payload
        else:
            # now, wait for what's coming in on the webhook
            header, payload = wait_for_message(key=key)
            return header, payload

    def asset_id_to_artifact_uri(self, asset_id: str):
        """
        Transform a regular asset_id into a valid artifact uri.
        """
        return f"urn:artifact:{asset_id}"

    def transfer(self, asset_id: str, agreement_id:str):
        """
        New version with only required params.

        Returns the provider EDR token
        """
        artifact_uri = self.asset_id_to_artifact_uri(asset_id=asset_id)
        daps_token = self._get_daps_token()
        access_token = daps_token['access_token']

        # actual data request
        header_msg = self.prepare_default_header(msg_type='ids:ArtifactRequestMessage', daps_access_token=access_token, provider_connector_ids_endpoint=self.connector_ids_endpoint, transfer_contract_id=agreement_id)
        header = json.loads(header_msg)
        header['ids:requestedArtifact'] = artifact_uri
        header['ids:transferContract'] = agreement_id
        header_msg = json.dumps(header)
        
        # TODO: this message seems to be NOT IDS compliant!
        artifact_request_message_payload = {
            'secret': '12345',
            'dataDestination': {
                'properties': {
                    'keyName': 'mydummykeyname',
                    'type': 'HttpProxy',
                    #'baseurl': 'http://localhost'
                }
            }
        }
        payload = json.dumps(artifact_request_message_payload)
        header_received, payload_received = self._send_message(header_msg=header_msg, payload=payload, provider_connector_ids_endpoint=self.connector_ids_endpoint)
        if self.debug_messages:
            self._debug_message(msg=header_received, fn='transfer_artifact_header.json')
            self._debug_message(msg=payload_received, fn='transfer_artifact_payload.json')
        # the received header is only relevant to get the correlation id under which we can find
        # the received (or soon to be received) provider EDR token
        correlation_id = header_received['ids:correlationMessage']['@id']
        # now, wait for what's coming in on the webhook
        edr_header, edr_payload = self.wait_for_message(key=correlation_id)
        return edr_payload
