# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from uuid import uuid4
from fastapi import APIRouter, Body, Request, HTTPException, status, Response

from pycxids.core.http_binding.models import ContractRequestMessage, ContractNegotiation, TransferProcess, TransferRequestMessage, NegotiationState, TransferState
from pycxids.core.http_binding.models_local import NegotiationStateStore, TransferStateStore
from pycxids.core.http_binding.settings import HTTP_HEADER_LOCATION, KEY_DATASET, KEY_MODIFIED, PROVIDER_DISABLE_IN_CONTEXT_WORKER, PROVIDER_STORAGE_AGREEMENTS_FN, PROVIDER_STORAGE_FN, PROVIDER_STORAGE_REQUESTS_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_STATE, PROVIDER_TRANSFER_STORAGE_FN
from pycxids.core.http_binding.transfer_provider_worker import transfer_transition_requested_started
from pycxids.utils.storage import FileStorageEngine
from pycxids.utils.tasks import fire_and_forget

storage_negotiation = FileStorageEngine(storage_fn=PROVIDER_STORAGE_FN, last_modified_field_name_isoformat=KEY_MODIFIED)
storage_transfer = FileStorageEngine(storage_fn=PROVIDER_TRANSFER_STORAGE_FN, last_modified_field_name_isoformat=KEY_MODIFIED)
storage_agreements = FileStorageEngine(storage_fn=PROVIDER_STORAGE_AGREEMENTS_FN, last_modified_field_name_isoformat=KEY_MODIFIED)

app = APIRouter(tags=['Transfer'])

@app.post('/transfers/request', response_model=TransferProcess)
async def transfer_request(request: Request, response: Response):
    """
    Look into the negotatiation process first if already in proper state to start the transfer.

    Generate a new id for the transfer (don't use the one given from the consumer).

    Store and provide a api key.
    Also store the lifteime of the api key.

    In the future, use a JWT token

    Asyncronously send the response to the given callbackAddress
    """
    body = await request.json()
    with open('transfer_request_message.json', 'wt') as f:
        body_str = json.dumps(body, indent=4)
        f.write(body_str)

    msg_process_id = body.get('dspace:processId')
    msg_id = body.get('@id')
    process_id = msg_id
    if msg_process_id:
        # this is EDC issue https://github.com/eclipse-edc/Connector/issues/3253
        process_id = msg_process_id
    transfer_request_message = TransferRequestMessage.parse_obj(body)
    # check some bar minimum prerequisites
    if not transfer_request_message.dspace_agreement_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="agreementId rquired!")
    if not transfer_request_message.dspace_callback_address:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="callbackAddress required!")

    # find the corresponding negotitation
    negotiation_id = storage_agreements.get(transfer_request_message.dspace_agreement_id)
    if not negotiation_id:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f"No negotiation available for given agreementId: {transfer_request_message.dspace_agreement_id}",
        )
    negotiation: NegotiationStateStore = NegotiationStateStore.parse_obj(storage_negotiation.get(negotiation_id, {}))
    if not negotiation.state in [NegotiationState.agreed, NegotiationState.verified, NegotiationState.finalized]:
        # for now, agreed state is enough
        # TODO: later we should check for finalized only
        raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail=f"Given negotiation not in correct state to start the transfer. State: {negotiation.state}")

    if not negotiation.agreement_id or negotiation.agreement_id != transfer_request_message.dspace_agreement_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Negotiation storage does not contain an agreement_id or is different to the requested one.")

    # generate a unique id
    transfer_id = str(uuid4())

    state_store = TransferStateStore(
        id = transfer_id,
        process_id = process_id,
        state = TransferState.requested,
        agreement_id = negotiation.agreement_id,
        callback_address_request = transfer_request_message.dspace_callback_address,
    )


    storage_transfer.put(transfer_id, state_store.dict())

    if not PROVIDER_DISABLE_IN_CONTEXT_WORKER:
        task = asyncio.create_task(transfer_transition_requested_started(item=state_store, negotiation_state=negotiation))
        fire_and_forget(task=task)

    transfer_process = TransferProcess(
        field_id = transfer_id,
        dspace_process_id = transfer_request_message.field_id,
        dspace_state = state_store.state,
    )
    response.headers[HTTP_HEADER_LOCATION] =  f"/transfers/{transfer_id}"
    return transfer_process

@app.post('/transfers/{id}/completion')
async def transfer_request(request: Request, id: str):
    print(f"/transfers/{id}/completion")
    return {}

@app.get('/transfers/{id}', response_model=TransferProcess)
def get_transfer_process(id: str):
    transfer_id = id
    transfer_data = storage_transfer.get(transfer_id)
    if not transfer_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    state_store: TransferStateStore = TransferStateStore.parse_obj(transfer_data)
    transfer_process = TransferProcess(
        field_id = state_store.id,
        dspace_process_id = state_store.process_id,
        dspace_state = state_store.state,
    )
    return transfer_process
