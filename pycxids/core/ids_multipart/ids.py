# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from email.message import EmailMessage
import json
from threading import Thread
import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from datetime import datetime
import base64
import sys
from string import Template
import requests
from uuid import uuid4
from email import message_from_bytes, message_from_string
from requests_toolbelt.multipart import decoder
import uvicorn

from pycxids.core import jwt_decode
from pycxids.core.ids_multipart import message_templates
from pycxids.core.ids_multipart.multipart_helper import parse_multipart_result, prepare_default_header, prepare_multipart_msg, prepare_multipart_msg_by_str, send_message
from pycxids.core.settings import ASSERTION_TYPE, CERT_FN, CLIENT_ID, CONSUMER_CONNECTOR_URL, CONSUMER_CONNECTOR_URN, CONSUMER_WEBHOOK, DAPS_ENDPOINT, SCOPE, settings
from pycxids.core.daps import get_daps_token
from pycxids.core.ids_multipart.webhook_queue import wait_for_message


def get_catalog(daps_token: str, provider_connector_ids_endpoint: str, resource_uri: str = '', paging_from: int = 0, paging_to: int = 0):
    """
    resource_ur: urn:resource:xxx
    """
    """
    # this is IDS protocol to limit the result - which is not yet working in EDC
    # https://github.com/International-Data-Spaces-Association/IDS-G/blob/main/Communication/Message-Types/README.md#idsdescriptionrequestmessage
    if resource_uri:
        catalog_req_msg['ids:requestedElement'] = resource_uri

    """

    header_msg = prepare_default_header(msg_type='ids:DescriptionRequestMessage', daps_access_token=daps_token['access_token'], provider_connector_ids_endpoint=provider_connector_ids_endpoint)

    # this is the EDC implementation to do paging - not standardized!
    if paging_from != 0 and paging_to != 0:
        header = json.loads(header_msg)
        header['from'] = paging_from
        header['to'] = paging_to
        header_msg = json.dumps(header)
    """
    # this is an IDS feature that seems not being supported in EDC
    header = json.loads(header_msg)
    header['ids:requestedElement'] = 'urn:uuid:028aaea9-ac01-4838-a516-00ef604ef128-urn:uuid:1b0a70a0-f64b-4c45-a808-4d35d3912fe5'
    header_msg = json.dumps(header)
    """

    # for debugging only
    with(open('request.json', 'w')) as f:
        f.write(header_msg)

    header_received, payload_received = send_message(header_msg=header_msg, provider_connector_ids_endpoint=provider_connector_ids_endpoint)
    return header_received, payload_received

def negotiate(daps_token:str, contract_offer: dict, provider_connector_ids_endpoint: str):

    access_token = daps_token['access_token']
    transfer_contract_id = str(uuid4())
    header_msg = prepare_default_header(msg_type='ids:ContractRequestMessage', daps_access_token=access_token, provider_connector_ids_endpoint=provider_connector_ids_endpoint, transfer_contract_id=transfer_contract_id)
    #print(header_msg)

    contract_request = {
        '@type': 'ids:ContractRequest',
        '@id': contract_offer['ids:contractOffer'][0]['@id'],
        'ids:permission':  contract_offer['ids:contractOffer'][0]['ids:permission'],
        'ids:provider': contract_offer['ids:contractOffer'][0]['ids:provider'],
        'ids:consumer': contract_offer['ids:contractOffer'][0]['ids:consumer'],
    }

    payload = json.dumps(contract_request)
    #print(json.dumps(contract_request, indent=4))
    header_received, payload_received = send_message(header_msg=header_msg, payload=payload, provider_connector_ids_endpoint=provider_connector_ids_endpoint)

    correlation_id = transfer_contract_id
    # now, wait for what's coming in on the webhook
    agreement_header, agreement_payload = wait_for_message(key=correlation_id)
    return agreement_header, agreement_payload

def transfer(resource_uri:str, artifact_uri:str, agreement: dict, daps_access_token: str, provider_connector_ids_endpoint: str):
    # first step is the same as with fetching the catalog for 1 resource!!!
    header_msg = prepare_default_header(msg_type='ids:DescriptionRequestMessage', daps_access_token=daps_access_token, provider_connector_ids_endpoint=provider_connector_ids_endpoint)
    header = json.loads(header_msg)
    header['ids:requestedElement'] = resource_uri # TODO: further ivestigation needed. 'r' vs 'R' is different

    header_msg = json.dumps(header)
    header_received, payload_received = send_message(header_msg=header_msg, payload='', provider_connector_ids_endpoint=provider_connector_ids_endpoint)
    #print(header_received)
    #print(payload_received)
    with (open('transfer_header.json', 'w')) as f:
        f.write(json.dumps(header_received, indent=4))
    with (open('transfer_payload.json', 'w')) as f:
        f.write(json.dumps(payload_received, indent=4))
    
    return header_received, payload_received

def request_data(ids_resource: dict, artifact_uri: str, agreement: dict, daps_access_token: str, contract_agreement_message: dict, provider_connector_ids_endpoint: str):
    # actual data request
    header_msg = prepare_default_header(msg_type='ids:ArtifactRequestMessage', daps_access_token=daps_access_token, provider_connector_ids_endpoint=provider_connector_ids_endpoint, transfer_contract_id=contract_agreement_message['ids:transferContract']['@id'])
    header = json.loads(header_msg)
    header['ids:requestedArtifact'] = artifact_uri
    header['ids:transferContract'] = agreement['@id']
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
    header_received, payload_received = send_message(header_msg=header_msg, payload=payload, provider_connector_ids_endpoint=provider_connector_ids_endpoint)
    with (open('transfer_artifact_header.json', 'w')) as f:
        f.write(json.dumps(header_received, indent=4))
    with (open('transfer_artifact_payload.json', 'w')) as f:
        f.write(json.dumps(payload_received, indent=4))

    return header_received, payload_received

