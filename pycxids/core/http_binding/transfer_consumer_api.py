# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from uuid import uuid4
from fastapi import APIRouter, Body, Request, HTTPException, status, Response

from pycxids.core.http_binding.models import ContractRequestMessage, ContractNegotiation, TransferProcess, TransferRequestMessage, NegotiationState, TransferStartMessage, TransferState
from pycxids.core.http_binding.models_local import NegotiationStateStore, TransferStateStore, DataAddress
from pycxids.core.http_binding.settings import CONSUMER_TRANSFER_STORAGE_FN, HTTP_HEADER_LOCATION, KEY_DATASET, KEY_MODIFIED, PROVIDER_DISABLE_IN_CONTEXT_WORKER, PROVIDER_STORAGE_AGREEMENTS_FN, PROVIDER_STORAGE_FN, PROVIDER_STORAGE_REQUESTS_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_STATE, PROVIDER_TRANSFER_STORAGE_FN
from pycxids.utils.jsonld import DEFAULT_DSP_REMOTE_CONTEXT, compact
from pycxids.utils.storage import FileStorageEngine




app = APIRouter(tags=['Transfer Common API - endponts for both, Consumer and Provider'])


@app.post('/transfers/{id}/start')
def post_transfer_start(id: str, body: dict = Body(...)):
    """
    Use on Consumer side

    Transitions:
    
    REQUESTED -> STARTED (Consumer only)

    TODO: is the provider transition similar enough to use it also on Provider side?
    """
    print(json.dumps(body, indent=4))
    body_c = compact(doc=body, context=DEFAULT_DSP_REMOTE_CONTEXT)
    transfer_start_message = TransferStartMessage.parse_obj(body_c)
    consumer_pid = transfer_start_message.dspace_consumer_pid
    # check some bar minimum prerequisites
    if not consumer_pid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="consumerPid rquired!")

    # not in S3 transfers
    # if not transfer_start_message.dspace_data_address:
    #     raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="dataAddress required!")

    # find the corresponding transfer
    if not CONSUMER_TRANSFER_STORAGE_FN:
        raise Exception("CONSUMER_TRANSFER_STORAGE_FN must be set!")
    
    storage_transfer = FileStorageEngine(storage_fn=CONSUMER_TRANSFER_STORAGE_FN, last_modified_field_name_isoformat=KEY_MODIFIED)

    storage_transfer.put(consumer_pid, transfer_start_message.dict())

    # result is a 200 ok
    return

@app.post('/transfers/{id}/termination')
def post_transfer_termination(id: str, body:dict = Body(...)):
    print(f"Transfer termination: {id}")
    return {}
