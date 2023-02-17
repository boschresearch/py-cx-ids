# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
import json
import requests
from fastapi import FastAPI, Request, Header, Body, Query, HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND


app = FastAPI(
        title="A HTTP Proxy to use as a Consumer Data Plane",
        description="Instead of special calls to the data plane, use this with regular HTTP_PROXY env var.",
    )


@app.get('{url:path}')
def proxy(request: Request, url: str):
    """
    """
    print(url)
    print(request)
    # TODO: continue here


if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8000')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.edc.consumer_proxy:app", host=host, port=int(port), workers=int(workers), reload=False)
