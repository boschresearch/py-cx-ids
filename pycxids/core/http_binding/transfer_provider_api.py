# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4
from fastapi import APIRouter, Body, Request, HTTPException, status

from pycxids.core.http_binding.models import ContractRequestMessage, ContractNegotiation, TransferProcess, TransferRequestMessage
from pycxids.core.http_binding.settings import KEY_DATASET, PROVIDER_DISABLE_IN_CONTEXT_WORKER, PROVIDER_STORAGE_FN, PROVIDER_STORAGE_REQUESTS_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_STATE
from pycxids.utils.storage import FileStorageEngine

storage = FileStorageEngine(storage_fn=PROVIDER_STORAGE_FN)

app = APIRouter(tags=['Transfer'])

@app.post('/transfers/request', response_model=TransferProcess)
def transfer_request(transfer_request_message: TransferRequestMessage = Body(...)):
    pass

@app.get('/transfers/{id}', response_model=TransferProcess)
def get_transfer_process(id: str):
    pass
