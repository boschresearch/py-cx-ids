# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path
from time import sleep
import json
from uuid import uuid4
import requests
from fastapi import FastAPI, Request, Header, Body, Query, HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND

from pycxids.edc.settings import CONSUMER_EDC_VALIDATION_ENDPOINT, CONSUMER_EDC_BASE_URL, CONSUMER_EDC_API_KEY
from pycxids.edc.api import EdcConsumer

from pycxids.utils.storage import FileStorageEngine

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
    """

    # Since the mapping is done via contract_id, we need to find this first
    edc = EdcConsumer(edc_data_managment_base_url=CONSUMER_EDC_BASE_URL, auth_key=CONSUMER_EDC_API_KEY)
    transfer = edc.get(path=f"/transferprocess/{transfer_process_id}")
    contract_id = transfer.get('dataRequest', {}).get('contractId', None)
    if not contract_id:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not find contract_id for given transfer_process_id: {transfer_process_id}")


    counter = 0
    while True:
        data = storage.get(key=contract_id)
        if data:
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
    r = requests.get(CONSUMER_EDC_VALIDATION_ENDPOINT, headers={'Authorization': consumer_edr_auth_code})
    if not r.ok:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not decode token transfer_process_id:{transfer_process_id}")

    decrypted_token = r.json()

    return decrypted_token['properties']

@app.post('/datareference')
def post_datareference(request: Request, body = Body(...)):
    cid = body.get('properties', {}).get('cid', '')
    if not cid:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not find cid in  properties.")
    storage.put(key=cid, value=body)
    return {}

if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8000')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.edc.token_receiver_service:app", host=host, port=int(port), workers=int(workers), reload=False)
