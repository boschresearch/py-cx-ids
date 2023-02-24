# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from fastapi import FastAPI, Depends, status, Security, Request, HTTPException, Query
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from fastapi.middleware.cors import CORSMiddleware

from pycxids.core.daps import get_daps_access_token, get_daps_token
from pycxids.core.jwt_decode import decode

BASIC_AUTH_USERNAME = os.getenv('BASIC_AUTH_USERNAME', 'admin')
BASIC_AUTH_PASSWORD = os.getenv('BASIC_AUTH_PASSWORD', None)
assert BASIC_AUTH_USERNAME, "BASIC_AUTH_PASSWORD must be set"
assert BASIC_AUTH_PASSWORD, "BASIC_AUTH_PASSWORD must be set"


app = FastAPI(title="Service to fetch a DAPS token")

# CORS configuration #
origins = [
    "*",
]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"])


def check_access(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    """
    Simple Basic Auth
    """
    try:
        if credentials.username == BASIC_AUTH_USERNAME and credentials.password == BASIC_AUTH_PASSWORD:
            return True
    except Exception as ex:
        print(ex)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Something went wrong with authentication.")


@app.get('/token', dependencies=[Security(check_access)])
def get_token(audience: str = Query(default='')):
    """
    Like a proxy to fetch a DAPS token from the real daps server.
    This can be used if the consumer application needs a DAPS token, to e.g. transfer it
    via a 'token' param to the provider backend system for further authentication.

    This is a workaround until the provider data plane is able to pass trusted requester information
    to the bakckend.
    """

    token = get_daps_token(audience=audience)
    return token

@app.get('/token-decoded', dependencies=[Security(check_access)])
def get_token_decoded(audience: str = Query(default='')):
    """
    Same as above, just decoded version of the access_token
    """
    token = get_daps_access_token(audience=audience)
    decoded_token = decode(token)
    decoded_token['signature'] = decoded_token['signature'].hex(':')
    return decoded_token


if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8000')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.services.daps_token_service:app", host=host, port=int(port), workers=int(workers), reload=False)
