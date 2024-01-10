# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from time import sleep
import json
import requests
from fastapi import FastAPI, Request, Body, Query, HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND

from pycxids.edc.settings import CONSUMER_EDC_VALIDATION_ENDPOINT

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
    Raises an expetion after timeout
    """
    counter = 0
    while True:
        data = storage.get(key=transfer_process_id)
        if data:
            return data
        
        if counter < timeout:
            sleep(1)
            counter = counter + 1
        else:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Ran into given timeout: {timeout} for id: {transfer_process_id}")

@app.get('/transfer/{transfer_process_id}/token/provider', deprecated=True)
def get_transfer_token_plain(transfer_process_id: str, timeout: int = Query(default=30, description='Timeout to wait for an EDR token before returning with an error')):
    """
    Return the decrypted version of the consumer EDR token 'authCode' - which is the (still) encrypted provider EDR token
    Deprecated: Tokens are no longer token-in-token. Always use the .../consumer endpoint
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

@app.post('/datareference', deprecated=True)
def post_datareference_dprecated(request: Request, body = Body(...)):
    """
    Deprecated. Use /transfer/datareference instead to have the same base url.
    """
    return post_datareference(request, body)

@app.post('/transfer/datareference')
def post_datareference(request: Request, body = Body(...)):
    """
    store with @id which is the transfer process id (it seems)
    Hint: cid (contract id) is no longer used by EDC as a reference (0.5.3)
    """
    storage_id = None
    if not storage_id:
        storage_id = body.get('id')
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
