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
STORAGE_FN = os.getenv('STORAGE_FN', 'transfer_service_storage.json')

storage = FileStorageEngine(storage_fn=STORAGE_FN)

app = FastAPI(
        title="EDC Consumer Transfer Service",
        description="Workaround for EDC limitations with a single endpoint to receive EDR tokens.",
    )


@app.get('/transfer/{asset_id}/{contract_negotiation_id}')
def get_transfer(request: Request, asset_id: str, contract_negotiation_id: str):
    # TODO: use /contractagreements/{id} instead of /contractnegotiations

    edc = EdcConsumer(edc_data_managment_base_url=CONSUMER_EDC_BASE_URL, auth_key=CONSUMER_EDC_API_KEY)
    contract_negotiation = edc.get(path=f"/contractnegotiations/{contract_negotiation_id}")

    if not contract_negotiation:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Could not find item for given contract_negotiation_id")
    state = contract_negotiation.get('state', '')
    if state != 'CONFIRMED':
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Requested contract negotiation is not yet in CONFIRMED state!")

    agreement_id = contract_negotiation.get('contractAgreementId')
    provider_endpoint = contract_negotiation.get('counterPartyAddress')

    data = storage.get(key=agreement_id)
    if data:
        return data

    if not provider_endpoint:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not lookup provider_endpoint")

    # if not yet available, start the transfer process
    transfer_id = edc.transfer(provider_ids_endpoint=provider_endpoint, asset_id=asset_id, agreement_id=agreement_id)
    # and try again
    TRANSFER_SERVICE_TIMEOUT = int(os.getenv('TRANSFER_SERVICE_TIMEOUT', '30'))
    counter = 0
    while True:
        data = storage.get(key=agreement_id)
        if data:
            return data
        
        if counter >= TRANSFER_SERVICE_TIMEOUT:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Could not find received EDR token. Timeout: {TRANSFER_SERVICE_TIMEOUT}")
        counter = counter + 1
        print(f"sleeping to wait for token for agreementId: {agreement_id}")
        sleep(1)


@app.post('/datareference')
def post_datareference(request: Request, body = Body(...)):
    cid = body.get('properties', {}).get('cid', '')
    if not cid:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not find cid in  properties.")
    # extract from consumer EDR
    consumer_edr_auth_code = body.get('authCode', None)
    r = requests.get(CONSUMER_EDC_VALIDATION_ENDPOINT, headers={'Authorization': consumer_edr_auth_code})
    if not r.ok:
        pass

    provider_edr = r.json()

    edr_combined = {
        'consumer_edr': body,
        'provider_edr': provider_edr['properties'],
    }
    storage.put(key=cid, value=edr_combined)
    return {}

if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8000')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.demo.assetstructure.transfer_service:app", host=host, port=int(port), workers=int(workers), reload=False)
