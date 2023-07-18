# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta
import json 
import os
from uuid import uuid4
import base64
from fastapi import FastAPI, Body, HTTPException, Header, Request, APIRouter, Query, status
import jwt
from jwcrypto.jwk import JWKSet, JWK
from jwcrypto.jwt import JWT

from pycxids.core.http_binding.crypto_utils import generate_rsa_key
from pycxids.core.jwt_decode import decode

router = APIRouter(tags=['MIW Mocks'])

key = generate_rsa_key()
private_key = JWK()
private_key.import_from_pyca(key=key)

def get_credentials_from_file(client_id: str):
    """
    Load credentials from file with given client_id
    """
    try:
        fn = os.path.join(os.path.dirname(__file__), f'miw_mock_credentials_{client_id}.json')
        data = ''
        with open(fn, 'rt') as f:
            data = f.read()
        credentials = json.loads(data)
        return credentials
    except Exception as ex:
        return None


@router.post('/miw/token')
async def get_token(request: Request):
    print(request.query_params)
    authorization = request.headers.get('authorization')
    client_id = None
    if authorization:
        # BASIC
        print(authorization)
        authorization = authorization.split(' ')[-1]
        auth_decoded = base64.b64decode(authorization).decode()
        print(auth_decoded)
        client_id = auth_decoded.split(':')[0]
    else:
        # transferred in body
        body = await request.body()
        body = body.decode()
        print(body)
        elements = body.split('&')
        for el in elements:
            kv = el.split('=')
            if kv[0] == 'client_id':
                client_id = kv[1]

    if not client_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No client_id given")
    now = datetime.now()
    header = {
        "kid": private_key.key_id,
        "typ": "at+jwt",
        "alg": "RS256"
    }
    payload = {
        "iss": "http://dev:9000",
        "sub": client_id,
        #"aud": 'audience',
        "jti": str(uuid4()),
        #"client_id": client_id,

        "exp" : int((now + timedelta(minutes=10)).timestamp()),
        "nbf": int(now.timestamp()),
        "iat": int(now.timestamp()),
    }
    token = JWT(header=header, claims=payload)

    token.make_signed_token(key=private_key)
    print(token)
    token_envelope = {
        "access_token": token.serialize(),
    }
    return token_envelope

def extract_client_id_from_auth_header(authorization: str):
    authorization = authorization.split(' ')[-1]
    auth_decoded = decode(data=authorization)
    client_id = auth_decoded.get('payload', {}).get('sub')
    return client_id

@router.get('/miw/api/credentials')
def get_credentials(request: Request, authorization: str = Header()):
    client_id = extract_client_id_from_auth_header(authorization)
    credentials = get_credentials_from_file(client_id=client_id)
    if not credentials:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find credentials for client_id: {client_id}")
    return credentials

@router.post('/miw/api/presentations')
def create_presentation(request: Request, audience: str = Query(), body: dict = Body(...), authorization: str = Header()):
    print(request.query_params)
    print(body)
    client_id = extract_client_id_from_auth_header(authorization)
    credentials = get_credentials_from_file(client_id=client_id).get('content')
    now = datetime.now()
    payload = {
        "sub": "did:web:something:BPNLconsumer",
        "aud": audience,
        "iss": "did:web:something:BPNLconsumer",
        "vp": {
            "id": "did:web:something:BPNLconsumer#c47a04e0-13b3-4e14-b576-4c1d197bb5fb",
            "type": [
                "VerifiablePresentation"
            ],
            "@context": [
                "https://www.w3.org/2018/credentials/v1"
            ],
            "verifiableCredential": credentials,
        },
        "exp" : int((now + timedelta(minutes=10)).timestamp()),
        "jti": str(uuid4()),
    }
    header = {
        "kid": private_key.key_id,
        "typ": "at+jwt",
        "alg": "RS256" # should be EdDSA... does EDC check? TODO: continue here, signature could be the issue
    }
    token = JWT(header=header, claims=payload)

    token.make_signed_token(key=private_key)
    print(token)
    token_envelope = {
        "vp": token.serialize(),
    }
    return token_envelope
    return {}

@router.post('/miw/api/presentations/validation')
def validate_presentation(request: Request, body: dict = Body(...)):
    vp = body.get('vp')
    result = {
        'valid': True,
        'vp': vp,
    }
    return result


app = FastAPI(title='Standalone MIW Mocks')
app.include_router(router)

if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '9000')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.miw.miw_server:app", host=host, port=int(port), workers=int(workers), reload=False)
