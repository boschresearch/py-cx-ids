# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
import json
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Security, status, Depends, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import jwt
from jwt import PyJWKClient
from pycxids.core.settings import settings

app = FastAPI(title="CX Testdata Submodel Endpoint Server for R1")

# CORS configuration #
origins = [
    "*",
]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"])

authoritation_header = APIKeyHeader(name='Authorization', auto_error=False) #auto_error only check if key exists!

def check_authorization(authorization: str = Security(authoritation_header)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"No Authorization header given.")

    try:
        jwt_token = authorization
        if jwt_token.lower().startswith('bearer'):
            jwt_token = jwt_token.split(' ')[1]

        jwks_client = PyJWKClient(settings.DAPS_JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(jwt_token)
        decoded_token = jwt.decode(jwt_token, signing_key.key, algorithms=["RS256"], options={'verify_aud': False}) # TODO: audience
        #print(decoded_token)
        path = urlparse(decoded_token['referringConnector']).path

        bpn = path.split('/')[-1]

        return bpn
    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Could not verify jwt token.")

#@app.get('/', dependencies=[Security(check_authorization)])
@app.get('/')
def hello_world(bpn: dict = Depends(check_authorization)):
    print(bpn)
    headers = {
        'Policy-IDS': 'http://localhost:8080/policy/cdfd26aaf5b1fdc6d71af7c1349869f9314b67626bc1eec44e64af674e357eed'
    }
    r = Response(content=f'BPN verified via DAPS token: {bpn}', status_code=status.HTTP_200_OK, headers=headers)
    return r

@app.get('/policy/{policy_hash}')
def get_policy(policy_hash: str):
    fn = os.path.join('policies', policy_hash + '.json')
    if not os.path.exists(fn):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not policy with id / hash: {policy_hash}")
    return FileResponse(fn, media_type='application/octet-stream')

if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8080')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.cdelight.server:app", host=host, port=int(port), workers=int(workers), reload=False)

