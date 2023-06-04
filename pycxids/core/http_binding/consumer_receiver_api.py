# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from time import sleep
from fastapi import APIRouter, Body, Request, HTTPException, status, Query

from pycxids.core.http_binding.settings import CONSUMER_STORAGE_AGREEMENTS_RECEIVED_FN, KEY_MODIFIED
from pycxids.utils.storage import FileStorageEngine

storage_agreements_received = FileStorageEngine(storage_fn=CONSUMER_STORAGE_AGREEMENTS_RECEIVED_FN, last_modified_field_name_isoformat=KEY_MODIFIED)

app = APIRouter(tags=['Negotiaion Consumer - customized, non-dsp / private receiver API'])

@app.get('/negotiations/{id}/agreement')
def get_negotiation_agreement(id: str, timeout: int = Query(default=30, description='Timeout to wait for a message before returning with an error')):
    """
    TODO: Needs to be private / protected in the future!

    This is a receiver servcie that allows consumer client applications to not open its own public endpoint
    to receive messages.
    """
    counter = 0
    while True:
        data = storage_agreements_received.get(id)
        if data:
            return data
        if counter < timeout:
            sleep(1)
            counter = counter + 1
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ran into given timeout: {timeout} for id: {id}")
