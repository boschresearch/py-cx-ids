# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path
from time import sleep
from datetime import datetime
import json
from uuid import uuid4
import requests
from fastapi import FastAPI, Request, Header, Body, Query, HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND

from pycxids.edc.settings import CONSUMER_EDC_VALIDATION_ENDPOINT, CONSUMER_EDC_BASE_URL, CONSUMER_EDC_API_KEY, USE_V1_DATA_MANAGEMENT_API
from pycxids.edc.api import EdcConsumer

from pycxids.utils.storage import FileStorageEngine
from pycxids.core.jwt_decode import decode

# TODO: not thread / process safe. Don't use with multiple uvicorn workers for now
STORAGE_FN = os.getenv('STORAGE_FN', 'token_receiver_service.json')
storage = FileStorageEngine(storage_fn=STORAGE_FN)


app = FastAPI(
        title="EDC Consumer Token Receiver Service",
        description="Workaround for EDC limitations with a single endpoint to receive EDR tokens.",
    )


@app.get('/transfer/{transfer_process_id}/token/consumer')
def get_transfer_token(transfer_process_id: str, timeout: int = Query(default=30, description='Timeout to wait for an EDR token before returning with an error')):
    """
    Waits until timeout and checks every second if an EDR token has been received.
    Returns the consumer EDR token
    Raises an expetion if token is no longer valid. A new transfer needs to be started in such cases.
    """

    # Since the mapping is done via contract_id, we need to find this first
    edc = EdcConsumer(edc_data_managment_base_url=CONSUMER_EDC_BASE_URL, auth_key=CONSUMER_EDC_API_KEY)
    contract_id = None
    if USE_V1_DATA_MANAGEMENT_API:
        transfer = edc.get(path=f"/transferprocess/{transfer_process_id}")
        contract_id = transfer.get('dataRequest', {}).get('contractId', None)
    else:
        transfer = edc.get(path=f"/transferprocesses/{transfer_process_id}")
        contract_id = transfer.get('edc:dataRequest', {}).get('edc:contractId', None)
    if not contract_id:
        print(f"Could not find contract_id for given transfer_process_id: {transfer_process_id}")
        print(f"Using transfer_process_id for now: {transfer_process_id}")
        contract_id = transfer_process_id # TODO: fix this later
        #raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not find contract_id for given transfer_process_id: {transfer_process_id}")

    print(f"transfer_process_id: {transfer_process_id}, contract_id: {contract_id}")

    counter = 0
    while True:
        data = storage.get(key=contract_id)
        if not data:
            # seems to be the case in product-edc 0.5.0-RC5 we don't get the cid anymore and thus, we
            # use the @id which seems to be the transfer_process_id
            data = storage.get(key=transfer_process_id)
        if data:
            # once there is data, we should check if the token is still valid before we return it
            decoded_data = decode(data.get('authCode'))
            #print(decoded_data)
            exp = decoded_data.get('payload', {}).get('exp', None)
            if not exp:
                raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not find exp in token.")
            now = datetime.now().timestamp()
            if now > exp:
                error_msg = f"Token no longer valid. exp: {exp} now: {now}"
                print(error_msg)
                raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)

            return data
        
        if counter < timeout:
            sleep(1)
            counter = counter + 1
        else:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Ran into given timeout: {timeout} for id: {transfer_process_id}")

@app.get('/transfer/{transfer_process_id}/token/provider')
def get_transfer_token_plain(transfer_process_id: str, timeout: int = Query(default=30, description='Timeout to wait for an EDR token before returning with an error')):
    """
    Return the decrypted version of the consumer EDR token 'authCode' - which is the (still) encrypted provider EDR token
    """
    token = get_transfer_token(transfer_process_id=transfer_process_id, timeout=timeout)

    # extract from consumer EDR
    consumer_edr_auth_code = token.get('authCode', None)
    #validation_endpoint = CONSUMER_EDC_BASE_URL.replace('/v2', '') + '/token'
    #if USE_V1_DATA_MANAGEMENT_API:
    validation_endpoint = CONSUMER_EDC_VALIDATION_ENDPOINT
    r = requests.get(validation_endpoint, headers={'Authorization': consumer_edr_auth_code})
    if not r.ok:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not decode token transfer_process_id:{transfer_process_id}")

    decrypted_token = r.json()

    return decrypted_token['properties']

@app.post('/datareference')
def post_datareference_dprecated(request: Request, body = Body(...)):
    """
    Deprecated. Use /transfer/datareference instead to have the same base url.
    """
    return post_datareference(request, body)

@app.post('/transfer/datareference')
def post_datareference(request: Request, body = Body(...)):
    """
    If cid (contractId) ist NOT available, store with @id which is the transfer process id (it seems)
    """
    storage_id = None
    cid = body.get('properties', {}).get('cid', '')
    if not cid:
        # DSP protocol / product-edc 0.4.x and higher
        cid = body.get('properties', {}).get('https://w3id.org/edc/v0.0.1/ns/cid', '')
    storage_id = cid
    if not storage_id:
        storage_id = body.get('id')
    print(f"cid: {cid}")
    print(f"stoarage_id: {storage_id}")
    storage.put(key=storage_id, value=body)
    print(json.dumps(body, indent=4))
    return {}

if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8000')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.edc.token_receiver_service:app", host=host, port=int(port), workers=int(workers), reload=False)
