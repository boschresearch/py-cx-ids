# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from uuid import uuid4
from fastapi import APIRouter, Body, Header, Request, HTTPException, status

from pyld import jsonld
from pycxids.utils.jsonld import default_context

from pycxids.core.jwt_decode import decode
from pycxids.core.http_binding.models import ContractAgreementVerificationMessage, ContractRequestMessage, ContractNegotiation, NegotiationState
from pycxids.core.http_binding.settings import KEY_DATASET, KEY_MODIFIED, KEY_PROCESS_ID, PROVIDER_DISABLE_IN_CONTEXT_WORKER, PROVIDER_STORAGE_FN, PROVIDER_STORAGE_REQUESTS_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_STATE
from pycxids.utils.storage import FileStorageEngine
from pycxids.core.http_binding.negotiation_provider_worker import requested_agreed, verified_finalized
from pycxids.utils.tasks import fire_and_forget

storage = FileStorageEngine(storage_fn=PROVIDER_STORAGE_FN)
storage_negotiation_requests = FileStorageEngine(storage_fn=PROVIDER_STORAGE_REQUESTS_FN, last_modified_field_name_isoformat=KEY_MODIFIED)

app = APIRouter(tags=['Negotiaion'])

@app.post('/negotiations/request', response_model=ContractNegotiation)
async def negotiation_request(request: Request, authorization: str = Header(...)):
    body = await request.json()
    auth_token = decode(data=authorization)
    with open('contract_request_message.json', 'wt') as f:
        body_str = json.dumps(body, indent=4)
        f.write(body_str)
    expanded = jsonld.expand(body)
    our_compacted = jsonld.compact(expanded, ctx=default_context, options={'compactArrays': True})
    offer = body.get('dspace:offer')
    contract_request: ContractRequestMessage = ContractRequestMessage.parse_obj(body)
    contract_request.dspace_offer.odrl_obligation = []
    contract_request.dspace_offer.odrl_prohibition = []
    if not contract_request.field_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='no @id field given.')
    if storage_negotiation_requests.get(contract_request.field_id):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='@id already exists')
    # store the original request
    storage_negotiation_requests.put(contract_request.field_id, contract_request.dict())
    dataset_id = contract_request.dspace_dataset
    if not dataset_id:
        # this is an issue in the spec and therefore we need to check for EDC field name here
        # https://github.com/eclipse-edc/Connector/issues/3237
        # https://github.com/International-Data-Spaces-Association/ids-specification/issues/127
        dataset_id = contract_request.dspace_data_set
    # don't use the consumers' id, but generate a new one under which we process the request
    id = str(uuid4())
    # store for further processing
    custom_storage_item = {
        KEY_ID: id,
        KEY_STATE: NegotiationState.requested,
        KEY_NEGOTIATION_REQUEST_ID: contract_request.field_id,
        KEY_DATASET: dataset_id,
        KEY_PROCESS_ID: contract_request.dspace_process_id,
    }
    storage.put(id, custom_storage_item)
    if not PROVIDER_DISABLE_IN_CONTEXT_WORKER:
        # sends and immediate agreed response to the consumer
        task = asyncio.create_task(requested_agreed(item=custom_storage_item, offer=offer))
        fire_and_forget(task=task)
    # prepare response
    contract_negotiation = ContractNegotiation(
        field_id = id,
        dspace_process_id=contract_request.field_id, # this is a consumer id and used as a correlation id
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

@app.post('/negotiations/{id}/agreement/verification')
async def negotiation_agreement(request: Request, id: str):
    """
    We just confirm every message we received. No matter we know it or not.
    We store it and send a 200 OK, which means state is transitioned to 'VERIFIED'
    """
    body = await request.json()
    with open('contract_agreement_verification_message.json', 'wt') as f:
        body_str = json.dumps(body, indent=4)
        f.write(body_str)

    # TODO: verify signature on the agreement

    if not PROVIDER_DISABLE_IN_CONTEXT_WORKER:
        # sends and immediate agreed response to the consumer
        task = asyncio.create_task(verified_finalized(id=id, msg=body))
        fire_and_forget(task=task)

    return {}

@app.post('/negotiations/{id}/termination')
async def negotiation_agreement(request: Request, id: str):
    print(f"Termination of contract / negotiation with id: {id}")
    return {}