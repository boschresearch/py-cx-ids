# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4
from fastapi import APIRouter, Body, Request, HTTPException, status

from pycxids.core.http_binding.models import ContractOfferMessage, ContractAgreementMessage, NegotiationState
from pycxids.core.http_binding.settings import KEY_DATASET, KEY_MODIFIED, PROVIDER_STORAGE_FN, CONSUMER_STORAGE_AGREEMENTS_RECEIVED_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_STATE
from pycxids.utils.storage import FileStorageEngine

storage_agreements_received = FileStorageEngine(storage_fn=CONSUMER_STORAGE_AGREEMENTS_RECEIVED_FN, last_modified_field_name_isoformat=KEY_MODIFIED)

app = APIRouter(tags=['Negotiaion Consumer'])

@app.post('/negotiations/{id}/offers')
def negotiation_offer(id: str, contract_offer: ContractOfferMessage = Body(...)):
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Not implemented yet')

@app.post('/negotiations/{id}/agreement')
def negotiation_agreement(id: str, contract_agreement: ContractAgreementMessage = Body(...)):
    """
    We just confirm every agreement we received. No matter we know it or not.
    We store it and send a 200 OK, which means state is transitioned to 'AGREED'
    """
    process_id = contract_agreement.dspace_process_id
    data = contract_agreement.dict()
    storage_agreements_received.put(
        process_id, #id, as a consumer we might not know the id, but the process id
        data,
    )
    return {}

