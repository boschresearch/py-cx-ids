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
from pycxids.core.http_binding.crypto_utils import *
from pycxids.core.http_binding.settings import settings


app = APIRouter(tags=['Data Backend Demo'])

@app.get('/data/{id}')
def get_data(id: str, auth_code: str = Header(alias=HTTP_HEADER_DEFAULT_AUTH_KEY)):
    """
    Demo Data Backend
    """
    if not auth_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # first decrypt the authcode, because this was only encrypted for us
    private_key = None
    with open(settings.BACKEND_PRIVATE_KEY_PKCS8_FN, 'rb') as f:
        private_key = f.read()
    decrypted = ''
    try:
        decrypted = decrypt(payload=auth_code, private_key_pem=private_key)
    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not decrypt token!")
    # and verify the provider signature on the token
    # TODO: get this pub key from a jwks endpoint of the provider, not from the file
    provider_public_key = None
    with open(settings.PROVIDER_PUBLIC_KEY_PEM_FN, 'rb') as f:
        provider_public_key = f.read()
    verified_claims_str = ''
    try:
        verified_claims_str = verify(payload=decrypted, public_key_pem=provider_public_key)
    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not verify token signature!")
    print(verified_claims_str)
    verified_claims = json.loads(verified_claims_str)

    result = {
        'agreement_id': verified_claims.get('agreement_id'),
        'dataset_id': verified_claims.get('dataset_id'),
    }
    return result