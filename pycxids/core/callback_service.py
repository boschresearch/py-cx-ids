# Copyright (c) 2025 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


from time import sleep
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
