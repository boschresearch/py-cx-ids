# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
import json
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Security, status, Depends, Response, Header
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import jwt
from jwt import PyJWKClient
from pycxids.core.settings import settings

POLICY_DIR = os.getenv('POLICY_DIR', 'policies')

POLICY_HASH = "cdfd26aaf5b1fdc6d71af7c1349869f9314b67626bc1eec44e64af674e357eed"
POLICY_HEADER = "Policy"

app = FastAPI(title="PTT - Policy Transfer Token Demo")

# CORS configuration #
origins = [
    "*",
]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"])

authoritation_header = APIKeyHeader(name='Authorization', auto_error=False) #auto_error only check if key exists!

def decode_daps_token(jwt_token):
    jwks_client = PyJWKClient(settings.DAPS_JWKS_URL)
    signing_key = jwks_client.get_signing_key_from_jwt(jwt_token)
    decoded_token = jwt.decode(jwt_token, signing_key.key, algorithms=["RS256"], options={'verify_aud': False}) # TODO: audience
    return decoded_token


def check_authorization(authorization: str = Security(authoritation_header)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"No Authorization header given.")

    try:
        jwt_token = authorization
        if jwt_token.lower().startswith('bearer'):
            jwt_token = jwt_token.split(' ')[1]

        decoded_token = decode_daps_token(jwt_token=jwt_token)
        #print(decoded_token)
        path = urlparse(decoded_token['referringConnector']).path

        bpn = path.split('/')[-1]

        if not bpn:
            raise Exception("No BPN in the jwt token.")

        return bpn
    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Could not verify jwt token.")

def check_signed_policy(policy_token: str = Header(..., alias='policy')):
    """
    In this case we need a signed policy. To check the signature, we need a public key.
    Since we have a central auth service (DAPS) we can also re-use this. The client authenticates
    against the DAPS and everything transferred to there is signed with the client credentials.
    The DAPS then adds this information ('audience') to the DAPS token.

    For the server it is easier to verify the DAPS token, because this is only 1 public key and easier
    to fetch (running server...).
    """
    if not policy_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No policy given.")
    
    decoded_token = decode_daps_token(jwt_token=policy_token)
    aud = decoded_token.get('aud', [])
    if len(aud) != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="DAPS token needs to contain exactly 1 aud item that is the policy.")
    policy = aud[0]

    return policy
    

@app.head('/')
def head_hello_world():
    headers = {
        POLICY_HEADER: f"http://localhost:8080/policy/{POLICY_HASH}"
    }
    return Response(status_code=status.HTTP_200_OK, headers=headers)

@app.get('/')
def get_hello_world(bpn: dict = Depends(check_authorization)):
    print(bpn)
    headers = {
        POLICY_HEADER: f"http://localhost:8080/policy/{POLICY_HASH}"
    }
    r = Response(content=f'BPN verified via DAPS token: {bpn}', status_code=status.HTTP_200_OK, headers=headers)
    return r

@app.head('/requiressignedpolicy')
def head_requiressignedpolicy():
    headers = {
        POLICY_HEADER: f"http://localhost:8080/policy/{POLICY_HASH}"
    }
    return Response(status_code=status.HTTP_200_OK, headers=headers)

@app.get('/requiressignedpolicy')
def get_requiressignedpolicy(daps_signed_policy: str = Depends(check_signed_policy)):
    policy_for_this_endpoint = f"http://localhost:8080/policy/{POLICY_HASH}"
    if daps_signed_policy != policy_for_this_endpoint:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Given signed policy is not enough for this endpoint.")
    headers = {
        POLICY_HEADER: policy_for_this_endpoint
    }
    r = Response(content=f'Access granted.', status_code=status.HTTP_200_OK, headers=headers)
    return r

@app.get('/policy/{policy_hash}')
def get_policy(policy_hash: str):
    fn = os.path.join(POLICY_DIR, policy_hash + '.json')
    if not os.path.exists(fn):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find policy with id / hash: {policy_hash}")
    return FileResponse(fn, media_type='application/octet-stream')

if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8080')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.ptt.server:app", host=host, port=int(port), workers=int(workers), reload=False)

