# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4
from fastapi import APIRouter, Body, Request, HTTPException, status, Response, Header

from pycxids.core.http_binding.models import ContractRequestMessage, ContractNegotiation, TransferProcess, TransferRequestMessage, NegotiationState, TransferStartMessage, TransferState
from pycxids.core.http_binding.models_local import NegotiationStateStore, TransferStateStore
from pycxids.core.http_binding.settings import AUTH_CODE_REFERENCES_FN, HTTP_HEADER_DEFAULT_AUTH_KEY, HTTP_HEADER_LOCATION, KEY_DATASET, KEY_MODIFIED, PROVIDER_DISABLE_IN_CONTEXT_WORKER, PROVIDER_STORAGE_AGREEMENTS_FN, PROVIDER_STORAGE_FN, PROVIDER_STORAGE_REQUESTS_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_STATE, PROVIDER_TRANSFER_STORAGE_FN
from pycxids.utils.storage import FileStorageEngine




app = APIRouter(tags=['Data Backend Demo'])

@app.get('/data/{id}')
def get_data(id: str, auth_code: str = Header(alias=HTTP_HEADER_DEFAULT_AUTH_KEY)):
    """
    Demo Data Backend
    """
    auth_code_storage = FileStorageEngine(storage_fn=AUTH_CODE_REFERENCES_FN, last_modified_field_name_isoformat=KEY_MODIFIED)
    transfer_id = auth_code_storage.get(auth_code)
    if not auth_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if not transfer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    storage_transfer = FileStorageEngine(storage_fn=PROVIDER_TRANSFER_STORAGE_FN, last_modified_field_name_isoformat=KEY_MODIFIED)
    transfer_data = storage_transfer.get(transfer_id, {})
    transfer: TransferStateStore = TransferStateStore.parse_obj(transfer_data)
    if not transfer.state in TransferState.started:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail=f"Transfer must be in STARTED state, but is in {transfer.state}"
        )

    # TODO: check also the original dataset id before returning the data
    # TODO: use jwt, add all relevant information (relevant for the data backend) into the jwt
    # and encrypt it with the pub key of the data backend (in the provider transfer worker)
    # data backend should not do any additional checks on states, etc.

