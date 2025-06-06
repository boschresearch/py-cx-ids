# Copyright (c) 2025 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


from time import sleep
import requests
from fastapi import Body, FastAPI, HTTPException
from starlette.status import HTTP_404_NOT_FOUND
from pycxids.utils.storage import FileStorageEngine

app = FastAPI(title="Callback API Service", version='0.1')

storage = FileStorageEngine('./callbacks.json')

@app.post('/{id}/{path:path}')
async def catch_all_post(id: str, path: str, body = Body(...)):
    print(id)
    print(path)
    print(body)
    storage.put(id, body)
    return {}

@app.get('/{id}/get')
async def get_data_wait(id:str):
    data = storage.get(id)
    if not data:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    # TODO: SECURITY: delete after fetched once, because data contains sensitive information
    # TODO: delete not implemented in storage interface ;-)
    return data

###
# client side API
###

def wait_callback_result(id_url: str, timeout: int = 20, check_field_name: str = '', field_value: str = ''):
    """
    This can be used from clients to wait for a certain time with the above service API.
    check_field_name='type',
    field_value='TransferProcessStarted'
    """
    counter = 0
    while True:
        r = requests.get(f"{id_url}/get")
        if r.status_code == 200:
            j = r.json()
            if not check_field_name:
                return j
            else:
                if j.get(check_field_name) == field_value:
                    return j

        sleep(1)
        counter = counter + 1
        if counter > timeout:
            print(f"Callback service timeout reached.")
            return None
