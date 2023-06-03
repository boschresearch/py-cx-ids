# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4
from fastapi import APIRouter, Body, Request, HTTPException, status

from pycxids.core.http_binding.models import ContractRequestMessage, ContractNegotiation, NegotiationState
from pycxids.core.http_binding.settings import KEY_DATASET, PROVIDER_DISABLE_IN_CONTEXT_WORKER, PROVIDER_STORAGE_FN, PROVIDER_STORAGE_REQUESTS_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_STATE
from pycxids.utils.storage import FileStorageEngine
from pycxids.core.http_binding.negotiation_provider_worker import requested_agreed

storage = FileStorageEngine(storage_fn=PROVIDER_STORAGE_FN)
storage_negotiation_requests = FileStorageEngine(storage_fn=PROVIDER_STORAGE_REQUESTS_FN)

app = APIRouter(tags=['Negotiaion'])

@app.post('/negotiations/request', response_model=ContractNegotiation)
def negotiation_request(contract_request: ContractRequestMessage = Body(...)):
    if not contract_request.field_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='no @id field given.')
    if storage_negotiation_requests.get(contract_request.field_id):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='@id already exists')
    # store the original request
    storage_negotiation_requests.put(contract_request.field_id, contract_request.dict())
    # don't use the consumers' id, but generate a new one under which we process the request
    id = str(uuid4())
    # store for further processing
    custom_storage_item = {
        KEY_ID: id,
        KEY_STATE: NegotiationState.requested,
        KEY_NEGOTIATION_REQUEST_ID: contract_request.field_id,
        KEY_DATASET: contract_request.dspace_dataset,
    }
    storage.put(id, custom_storage_item)
    if not PROVIDER_DISABLE_IN_CONTEXT_WORKER:
        # sends and immediate agreed response to the consumer
        requested_agreed(item=custom_storage_item)
    # prepare response
    contract_negotiation = ContractNegotiation(
        field_id = id,
        dscpace_process_id=id, # is the correlcation to the incoming request
        dspace_state=NegotiationState.requested,
    )
    # TODO: fix type with default
    # TODO: set location header
    return contract_negotiation


@app.get('/negotiations/{id}', response_model=ContractNegotiation)
def negotiation_get(id: str):
    data = storage.get(id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find item for id: {id}")
    contract_negotiation = ContractNegotiation(
        field_id = id,
        dspace_process_id = data.get(KEY_NEGOTIATION_REQUEST_ID),
        dspace_state=data.get(KEY_STATE),
    )
    return contract_negotiation

