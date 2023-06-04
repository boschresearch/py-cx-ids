# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from time import sleep
from datetime import datetime
from uuid import uuid4
import requests
from fastapi import status
from pycxids.core.http_binding.models_local import DataAddress, TransferStateStore

from pycxids.core.http_binding.settings import KEY_AGREEMENT_ID, KEY_DATASET, KEY_STATE, PROVIDER_CALLBACK_BASE_URL, PROVIDER_STORAGE_AGREEMENTS_FN, PROVIDER_STORAGE_FN, PROVIDER_STORAGE_REQUESTS_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_MODIFIED, PROVIDER_TRANSFER_STORAGE_FN
from pycxids.utils.storage import FileStorageEngine
from pycxids.core.http_binding.models import TransferStartMessage, TransferState

storage_transfer = FileStorageEngine(storage_fn=PROVIDER_TRANSFER_STORAGE_FN, last_modified_field_name_isoformat=KEY_MODIFIED)


def transfer_transition_requested_started(item: TransferStateStore):
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
    auth_code = str(uuid4())
    data_address = DataAddress(
        auth_code = auth_code, # TODO:
        base_url = PROVIDER_CALLBACK_BASE_URL, # TODO: append asset id
    )
    data_address_str = json.dumps(data_address.dict(exclude_unset=False))
    transfer_start_message = TransferStartMessage(
        dspace_process_id = item.process_id,
        dspace_data_address = data_address_str
    )
    latest: TransferStateStore = TransferStateStore.parse_obj(storage_transfer.get(item.id))
    latest.data_address = data_address_str
    storage_transfer.put(item.id, latest)

    r = requests.post(url=item.callback_address_request, json=transfer_start_message.dict())
    if r.status_code != 200:
        print(f"Transfer requested -> started error. Consumer callback response: {r.status_code} - {r.reason} - {r.content}")
        return None
    
    latest.state = TransferState.started
    storage_transfer.put(item.id, latest)



def worker_loop():
    while True:
        all = storage_transfer.get_all()
        for item in all:
            # TODO: implement for transfer process
            pass

        sleep(2)


if __name__ == '__main__':
    worker_loop()
