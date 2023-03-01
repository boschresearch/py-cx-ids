# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Security, status, Request, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials


BASIC_AUTH_USERNAME = os.getenv('BASIC_AUTH_USERNAME', 'someuser')
BASIC_AUTH_PASSWORD = os.getenv('BASIC_AUTH_PASSWORD', 'somepassword')
assert BASIC_AUTH_USERNAME, "BASIC_AUTH_PASSWORD must be set"
assert BASIC_AUTH_PASSWORD, "BASIC_AUTH_PASSWORD must be set"


app = FastAPI(title="api-wrapper compatible re-implementation")

# CORS configuration #
origins = [
    "*",
]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"])


def check_access(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    """
    Simple Basic Auth as with the original api-wrapper
    """
    try:
        if credentials.username == BASIC_AUTH_USERNAME and credentials.password == BASIC_AUTH_PASSWORD:
            return True
    except Exception as ex:
        print(ex)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Something went wrong with authentication.")


@app.get('/api/service/{full_path:path}', dependencies=[Security(check_access)])
def get_endpoint(request: Request, full_path: str = Path('', description='{asset_id}/{sub_url}* - sub_url is optional'), provider_connector_url: str = Query(..., alias="provider-connector-url")):
    """
    To receive all possible sub_urls (path behind the asset_id) and still make it optional,
    it seems we need to parse / split ourselve.
    What we acutally want is: '/api/service/{asset_id}/{sub_url}' where sub_url is optional
    """
    sub_url = ''
    parts = full_path.split('/')
    asset_id = parts[0]
    if len(parts) > 1:
        pos = full_path.find('/')
        sub_url = full_path[pos+1:]

    #print(params)
    print(f"asset_id: {asset_id}")
    print(f"sub_url: {sub_url}")
    try:

    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ex))


def post_endpoint(path: str):
    pass


if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8080')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.apiwrapper.api_wrapper:app", host=host, port=int(port), workers=int(workers), reload=False)
