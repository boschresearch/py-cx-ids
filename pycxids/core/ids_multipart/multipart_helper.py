# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from uuid import uuid4
from string import Template
import requests
from requests_toolbelt.multipart import decoder

from pycxids.core.settings import ASSERTION_TYPE, CERT_FN, CLIENT_ID, CONSUMER_CONNECTOR_URL, CONSUMER_CONNECTOR_URN, CONSUMER_WEBHOOK, DAPS_ENDPOINT, SCOPE
from pycxids.core.ids_multipart import message_templates
from pycxids.core import jwt_decode


def prepare_multipart_msg(header: dict, payload: dict):
    """
    use result in requests 'files='
    """
    files = {}
    if header:
        files['header'] = json.dumps(header).encode()
    if payload:
        files['payload'] = json.dumps(payload).encode()
    return files

def prepare_multipart_msg_by_str(header: str, payload: str):
    """
    use result in requests 'files='
    """
    files = {}
    if header:
        files['header'] = header.encode()
    if payload:
        files['payload'] = payload.encode()
    return files

def prepare_default_header(msg_type: str, daps_access_token, provider_connector_ids_endpoint: str, transfer_contract_id: str = '') -> str:
    if not transfer_contract_id:
        transfer_contract_id = str(uuid4())

    header_msg = Template(message_templates.DEFAULT_HEADER_MESSAGE).substitute(
        msg_type = msg_type,
        message_id = str(uuid4()),
        security_token_id = str(uuid4()),
        daps_access_token = daps_access_token,
        transfer_contract_id = transfer_contract_id,
        connector_urn = CONSUMER_CONNECTOR_URN,
        webhook_url = CONSUMER_WEBHOOK,
        recipient_connector = provider_connector_ids_endpoint
    )
    return header_msg

def send_message(header_msg:str, provider_connector_ids_endpoint: str, payload:str = ''):
    files = prepare_multipart_msg_by_str(header=header_msg, payload=payload)

    headers= {
        "User-Agent": "pythonrequests",
    }
    r = requests.post(provider_connector_ids_endpoint, files=files, headers=headers)
    if not r.ok:
        print(f"Could not send message. Reason: {r.reason} Content: {r.content}")
        return None, None
    content = r.content
    header, payload = parse_multipart_result(content, r.headers['Content-Type'])
    #print(json.dumps(header, indent=4))
    #print(json.dumps(payload, indent=4))
    return header, payload

def parse_multipart_result(r_content, content_type:str):
    """
    Returns the header and payload
    header is always in json
    payload CAN be NO json, e.g. in case of an error the payload can be pure text (the error text)

    Check the header @type content to know if payload is an error.
    """
    content = r_content
    payload = None
    header = None
    multiparts = decoder.MultipartDecoder(content=content, content_type=content_type)
    for part in multiparts.parts:
        cdh = part.headers.get(b'Content-Disposition', None).decode()
        if not cdh:
            continue
        if 'name="header"' in cdh:
            # debugging purposes only
            header = part.text
            header_json = json.loads(header)
            #with open('message_header.json', 'w') as f:
            #    f.write(json.dumps(header_json, indent=4))
            dynamic_attriute_token = header_json.get('ids:securityToken', {}).get('ids:tokenValue')
            decoded_dat = jwt_decode.decode(dynamic_attriute_token, verify_signature=False)
            #print(json.dumps(decoded_dat, indent=4, default=str))
            header = header_json

        if 'name="payload"' in cdh:
            mycontent = part.text
            #with open('catalog_raw_result.txt', 'w') as f:
            #    f.write(mycontent)
            try:
                j = json.loads(mycontent)
                payload = j
            except:
                payload = mycontent

    return header, payload
