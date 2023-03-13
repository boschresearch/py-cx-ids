# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
import json
from threading import Thread
from datetime import datetime
from fastapi import FastAPI, Request, Response, Body, Depends, HTTPException, status, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from requests_toolbelt import MultipartEncoder
import requests
import time

from pycxids.core.settings import CONSUMER_CONNECTOR_URN, CONSUMER_WEBHOOK, BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD, settings
from pycxids.core.ids_multipart.ids_multipart import IdsMultipartConsumer, IdsMultipartBase
from pycxids.core.daps import Daps
from pycxids.core.ids_multipart.webhook_queue import add_message, wait_for_message

from pycxids.utils.storage import FileStorageEngine

STORAGE_FN = os.getenv('STORAGE_FN', 'storage.json')


storage = FileStorageEngine(storage_fn=STORAGE_FN)

TEST_MSG_KEY = 'TEST_MSG'
TEST_MSG = b'test_msg'

WEBHOOK_LOADED_KEY = 'WEBHOOK_LOADED'

app = FastAPI()
security = HTTPBasic()

@app.post("/webhook")
async def webhook(request: Request): #, body: dict = Body(...)
    body = await request.body()
    if body.startswith(TEST_MSG):
        # this is a test msg to let us figure out if webhook is reachable in general
        add_message(key=TEST_MSG_KEY, header=TEST_MSG, payload=TEST_MSG)
        return ''
    content_type = request.headers['Content-Type']
    header, payload = IdsMultipartBase.parse_multipart_result(r_content=body, content_type=content_type)
    #print(json.dumps(header, indent=4))
    #print(json.dumps(payload, indent=4))

    # we don't need to wait for sending the response below. This is only for the protocol part on the consumer side
    # we can alrady notify the main thread what we have received
    correlation_id = None
    header_type = header.get('@type', '')
    if header_type == 'ids:ParticipantUpdateMessage':
        correlation_id = payload['id'] # is this the transferContract id?
        print(json.dumps(payload))

    # send / notify waiting thread
    if not correlation_id:
        correlation_id = header.get('ids:correlationMessage', {}).get('@id', None)
        if not correlation_id:
            correlation_id = header['ids:transferContract']['@id']
    # thread communication of the received content
    add_message(key = correlation_id, header=header, payload=payload)
    # store received content to make is accessible via an api request
    storage.put(key=correlation_id, value={
        'header': header,
        'payload': payload
    })

    # TODO: we should check the content before confirming anything

    response_payload = ''
    response_header = ''

    ids_endpoint = header.get('idsWebhookAddress') # TODO: is this the correct audience? need to check
    daps = Daps(daps_endpoint=settings.DAPS_ENDPOINT, private_key_fn=settings.PRIVATE_KEY_FN, client_id=settings.CLIENT_ID)
    daps_token = daps.get_daps_token(audience=ids_endpoint)


    # TODO: we should check the content before we confirm ;-)
    #response_header = mh.prepare_default_header(msg_type='ids:ContractAgreementMessage', daps_access_token=daps_token['access_token'])
    """
    TODO: Check why it is a ProcessNotification and not a ContractAgreementMessage as documented here:
    https://github.com/International-Data-Spaces-Association/IDS-G/tree/6c3b57916ea1d2792b6a0447fafab7d23b65110a/Communication/sequence-diagrams/data-connector-to-data-connector#usage-contract-negotiation
    "If instead, the agreement is accepted, and the processing is successful, the Consumer returns an ids:ContractAgreementMessage including the ids:ContractAgreement to the Provider to confirm the validity."

    """

    consumer = IdsMultipartBase(consumer_connector_urn=CONSUMER_CONNECTOR_URN, consumer_connector_webhook_url=CONSUMER_WEBHOOK)
    response_header = consumer.prepare_default_header(msg_type='ids:MessageProcessedNotificationMessage', daps_access_token=daps_token['access_token'], provider_connector_ids_endpoint=ids_endpoint)
    response_payload = json.dumps(payload)

    fields = {
        'header': response_header.encode()
    }
    if response_payload:
        fields['payload']: response_payload.encode()

    m = MultipartEncoder(fields=fields)
    content = m.to_string()

    response = Response(content=content, headers={'Content-Type': m.content_type} )
    return response


@app.get('/messages/{message_id}')
def get_message(message_id: str, credentials: HTTPBasicCredentials = Depends(security), timeout: int = Query(default=30)):
    """
    message_id is the 'correlation_id' from the IDS multipart messages.
    what it is, depends on where in the process the message was received.
    """
    if not (credentials.username == BASIC_AUTH_USERNAME and credentials.password == BASIC_AUTH_PASSWORD):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not authenticated. Use basic auth.")

    counter = 0
    while True:
        data = storage.get(key=message_id, default=None)
        if data:
            return data

        if counter < timeout:
            time.sleep(1)
            counter = counter + 1
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Timeout. Could not find message in time. timeout: {timeout}")


@app.get('/messages')
def get_all_messages(credentials: HTTPBasicCredentials = Depends(security)):
    """
    """
    if not (credentials.username == BASIC_AUTH_USERNAME and credentials.password == BASIC_AUTH_PASSWORD):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not authenticated. Use basic auth.")
    result = storage.get_all()
    return result


def send_test_request(public_url:str):
    r = requests.post(public_url, data=TEST_MSG)
    if not r.ok:
        print(r.content)

def webhook_test(public_url: str):
    """
    This method is typically called from a separate thread as the above endpoint is running.

    Communication via queue.
    Needs to wait a bit to let the server threa start before the request
    """
    try:
        # instead of the sleep, we wait until we receive a message from the webhook thread
        webhook_loaded_ts, _ = wait_for_message(key=WEBHOOK_LOADED_KEY)
        test_thread = Thread(target=send_test_request, args=[public_url])
        test_thread.start()
        header, payload = wait_for_message(key=TEST_MSG_KEY)
        msg = payload
        if msg == TEST_MSG:
            return True
    except Exception as ex:
        print(ex)
        return False
    
    return False


# fastapi startup is before the startup.
# once we are here, I think we can consider its loaded, right?
# any better way to check and inform the other thread?
now = datetime.now().timestamp()
add_message(WEBHOOK_LOADED_KEY, now, now)

if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8000')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.core.ids_multipart.webhook_fastapi:app", host=host, port=int(port), workers=int(workers), reload=False)
