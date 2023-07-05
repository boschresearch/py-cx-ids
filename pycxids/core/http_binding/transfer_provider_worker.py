# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from time import sleep
from datetime import datetime
from uuid import uuid4
from base64 import b64decode
import requests
from fastapi import status
from pycxids.core.daps import Daps
from pycxids.core.settings import settings as core_settings
from pycxids.core.http_binding.auth_code_generator import generate_auth_code
from pycxids.core.http_binding.models_edc import AssetEntryNewDto
from pycxids.core.http_binding.models_local import DataAddress, NegotiationStateStore, TransferStateStore

from pycxids.core.http_binding.settings import settings, ASSET_PROP_BACKEND_PUBLIC_KEY, AUTH_CODE_REFERENCES_FN, KEY_AGREEMENT_ID, KEY_DATASET, KEY_STATE, PROVIDER_CALLBACK_BASE_URL, PROVIDER_STORAGE_AGREEMENTS_FN, PROVIDER_STORAGE_ASSETS_FN, PROVIDER_STORAGE_FN, PROVIDER_STORAGE_REQUESTS_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_MODIFIED, PROVIDER_TRANSFER_STORAGE_FN
from pycxids.utils.storage import FileStorageEngine
from pycxids.core.http_binding.models import TransferStartMessage, TransferState

storage_transfer = FileStorageEngine(storage_fn=PROVIDER_TRANSFER_STORAGE_FN, last_modified_field_name_isoformat=KEY_MODIFIED)
storage_assets = FileStorageEngine(storage_fn=PROVIDER_STORAGE_ASSETS_FN, last_modified_field_name_isoformat=KEY_MODIFIED)

async def transfer_transition_requested_started(item: TransferStateStore, negotiation_state: NegotiationStateStore):
    """
    Transfer process state transition

    REQUESTED -> STARTED

    https://github.com/International-Data-Spaces-Association/ids-specification/blob/main/transfer/transfer.process.protocol.md#transfer-process-states
    
    item: TransferStateStore

    - create a random authCode
    - store dataAddress (authCode, etc) for the transfer
    - send data back to the consumer via the callbackAddress
    - if successful, mark the state transition in the transfer storage ('started')
    """
    if item.state != TransferState.requested:
        return None

    # TODO: potential check before we give access / send access credentials
    auth_code_claims = {
        'agreement_id': item.agreement_id,
        'dataset_id': negotiation_state.dataset,
    }
    # use the public key from the created asset to encrypt the content
    # use the provider private key, to sign it befor ecnryption
    asset_data = storage_assets.get(negotiation_state.dataset)
    asset:AssetEntryNewDto = AssetEntryNewDto.parse_obj(asset_data)
    backend_pub_key_b64 = asset.asset.properties.get(ASSET_PROP_BACKEND_PUBLIC_KEY)
    backend_pub_key = b64decode(backend_pub_key_b64)
    signing_private_key = None
    with open(settings.PROVIDER_PRIVATE_KEY_PKCS8_FN, 'rb') as f:
        signing_private_key = f.read()
    auth_code = generate_auth_code(claims=auth_code_claims, encryption_public_key_pem=backend_pub_key, signing_private_key_pem=signing_private_key)
    data_address = DataAddress(
        edc_cid = negotiation_state.agreement_id, # required by EDC?
        edc_auth_code = auth_code, # TODO:
        edc_endpoint = asset.data_address.properties.get('baseUrl'),
        edc_id = item.process_id, # TODO: does EDC require the mapping here to the processId?
    )
    # data_address_str = json.dumps(data_address.dict(exclude_unset=False))
    data_address_data = data_address.dict()

    transfer_start_message = TransferStartMessage(
        dspace_process_id = item.process_id,
        dspace_data_address = data_address_data,
    )
    latest: TransferStateStore = TransferStateStore.parse_obj(storage_transfer.get(item.id))
    latest.data_address = data_address
    storage_transfer.put(item.id, latest.dict())
    # store a reference from auth_code -> transfer
    auth_code_storage = FileStorageEngine(storage_fn=AUTH_CODE_REFERENCES_FN)
    auth_code_storage.put(auth_code, item.id)

    callback = item.callback_address_request
    daps = Daps(daps_endpoint=core_settings.DAPS_ENDPOINT, private_key_fn=core_settings.PRIVATE_KEY_FN, client_id=core_settings.CLIENT_ID)
    token = daps.get_daps_token(audience=callback)
    headers = {
        'Authorization': token['access_token']
    }

    data = transfer_start_message.dict()

    r = requests.post(url=f"{callback}/transfers/{item.process_id}/start", json=data, headers=headers)
    if r.status_code != 200:
        print(f"Transfer requested -> started error. Consumer callback response: {r.status_code} - {r.reason} - {r.content}")
        return None
    
    latest.state = TransferState.started
    storage_transfer.put(item.id, latest.dict())



def worker_loop():
    while True:
        all = storage_transfer.get_all()
        for item in all:
            # TODO: implement for transfer process
            pass

        sleep(2)


if __name__ == '__main__':
    worker_loop()
