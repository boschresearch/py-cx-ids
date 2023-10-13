# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import os
from fastapi import APIRouter, Body, Request, HTTPException, status, Response
from fastapi.responses import FileResponse

app = APIRouter()

# A service that "catches all" an prints it for debugging

@app.post('/{path:path}')
async def post_all(request: Request, path: str):
    print(path)
    headers = request.headers.items()
    print(json.dumps(headers, indent=4))
    body = await request.body()
    print(body)

    return {}

@app.get('/{path:path}')
def get_all(request: Request, path: str):
    print(path)
    headers = request.headers.items()
    print(json.dumps(headers, indent=4))

    #dummy_fn = os.path.join(os.path.dirname(__file__), 'dummy_data.txt')
    #return FileResponse(path=dummy_fn)
    return {"hello": "world"}
