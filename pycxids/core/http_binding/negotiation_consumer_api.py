# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from uuid import uuid4
from fastapi import APIRouter, Body, Request, HTTPException, status

from pycxids.core.http_binding.models import ContractOfferMessage, ContractAgreementMessage, NegotiationState
from pycxids.core.http_binding.settings import KEY_DATASET, KEY_MODIFIED, PROVIDER_STORAGE_FN, CONSUMER_STORAGE_AGREEMENTS_RECEIVED_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_STATE
from pycxids.utils.jsonld import DEFAULT_DSP_REMOTE_CONTEXT, compact, default_context
from pycxids.utils.storage import FileStorageEngine

storage_agreements_received = FileStorageEngine(storage_fn=CONSUMER_STORAGE_AGREEMENTS_RECEIVED_FN, last_modified_field_name_isoformat=KEY_MODIFIED)

app = APIRouter(tags=['Negotiaion Consumer'])

@app.post('/negotiations/{id}/offers')
def negotiation_offer(id: str, contract_offer: ContractOfferMessage = Body(...)):
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Not implemented yet')

@app.post('/negotiations/{id}/agreement')
def negotiation_agreement(id: str, body: dict = Body(...)):
    """
    We just confirm every agreement we received. No matter we know it or not.
    We store it and send a 200 OK, which means state is transitioned to 'AGREED'
    """
    print(json.dumps(body, indent=4))
    body_c = compact(doc=body, context=DEFAULT_DSP_REMOTE_CONTEXT)
    contract_agreement = ContractAgreementMessage.parse_obj(body_c)
    assert id is not contract_agreement.dspace_consumer_pid, "The given ID in the path is not equal to the consumerPid! This violates the DSP spec."
    data = contract_agreement.dict()
    storage_agreements_received.put(
        id, #id, as a consumer we might not know the id, but the process id
        data,
    )
    return {}

@app.post('/negotiations/{id}/termination')
def negotiation_termination(id: str, body: dict = Body(...)):
    print(f"termination id: {id}")
    return {}
