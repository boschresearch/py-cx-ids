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
    transfer_start_message = TransferStartMessage.parse_obj(body)
    # check some bar minimum prerequisites
    if not transfer_start_message.dspace_process_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="processId rquired!")

    # not in S3 transfers
    # if not transfer_start_message.dspace_data_address:
    #     raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="dataAddress required!")

    # find the corresponding transfer
    if not CONSUMER_TRANSFER_STORAGE_FN:
        raise Exception("CONSUMER_TRANSFER_STORAGE_FN must be set!")
    
    storage_transfer = FileStorageEngine(storage_fn=CONSUMER_TRANSFER_STORAGE_FN, last_modified_field_name_isoformat=KEY_MODIFIED)

    transfer_id = transfer_start_message.dspace_process_id
    # if not in storage yet, just load an empty one
    # this can be the case, when the client did not 'inform' the callback server about this transfer
    # which is probably the default case
    transfer_storage_data = storage_transfer.get(transfer_id, {'id': transfer_id})    
    # if not transfer_storage_data:
    #     print(f"Could not find transfer storage with id: {transfer_id}")
    #     return
    transfer: TransferStateStore = TransferStateStore.parse_obj(transfer_storage_data)
    # if not transfer.state in [TransferState.requested, TransferState.suspended]:
    #     raise HTTPException(
    #         status_code=status.HTTP_412_PRECONDITION_FAILED,
    #         detail=f"Given transfer not in correct state to start the transfer. State: {transfer.state}"
    #     )
    
    # should be empty, at least in REQUESTED -> STARTED transition
    if transfer.data_address:
        print(f"WARNING: data_address already set to: {transfer.data_address}")
        if transfer_start_message.dspace_data_address:
            print(f"received new dataAddress is: {transfer_start_message.dspace_data_address}")
        print("TODO: Check this behavior in detail!")
    data_address_received = None
    if transfer_start_message.dspace_data_address and isinstance(transfer_start_message.dspace_data_address, str):
        data_address_received = DataAddress.parse_raw(transfer_start_message.dspace_data_address.encode())
    else:
        if transfer_start_message.dspace_data_address:
            data_address_received = DataAddress.parse_obj(transfer_start_message.dspace_data_address)
    transfer.data_address = data_address_received
    storage_transfer.put(transfer_id, transfer.dict())

    # result is a 200 ok
    return

@app.post('/transfers/{id}/termination')
def post_transfer_termination(id: str, body:dict = Body(...)):
    print(f"Transfer termination: {id}")
    return {}
