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


@app.post('/transfer/datareference')
def post_datareference(request: Request, body = Body(...)):
    """
    Only works with tx-edc 0.7.x
    """
    print(json.dumps(body, indent=4))
    payload = body.get("payload", {})
    transfer_process_id = payload.get("transferProcessId")
    if not transfer_process_id:
        print(f"Ignoring. No transfer_process_id. Not storing anything.")
        return {}

    data_address_properties = payload.get("dataAddress", {}).get("properties")
    if not data_address_properties:
        print(f"Ignoring. No data_address_properties given")
        return {}

    storage.put(key=transfer_process_id, value=data_address_properties)
    return {}

if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8000')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.edc.token_receiver_service:app", host=host, port=int(port), workers=int(workers), reload=False)
