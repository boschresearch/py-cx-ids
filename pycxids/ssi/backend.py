# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from fastapi import FastAPI, HTTPException, status, Security, Depends
from fastapi.security import APIKeyHeader
from jwt import PyJWKClient
import jwt

app = FastAPI()

JWKS_ENDPOINT = os.environ.get('JWKS_ENDPOINT', 'http://dev:5000/jwks.json')

authoritation_header = APIKeyHeader(name='Authorization', auto_error=False) #auto_error only check if key exists!

def check_authorization(authorization: str = Security(authoritation_header)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"No Authorization header given.")

    try:
        jwt_token = authorization
        if jwt_token.lower().startswith('bearer'):
            jwt_token = jwt_token.split(' ')[1]

        # we use jwt lib here, because it has a simple feature to work with JWKS endpoints
        jwks_client = PyJWKClient(JWKS_ENDPOINT)
        signing_key = jwks_client.get_signing_key_from_jwt(jwt_token)
        decoded_token = jwt.decode(jwt_token, signing_key.key, algorithms=["RS256", "EdDSA"], options={'verify_aud': False})
        return decoded_token

    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Could not verify jwt token.")


@app.get('/protected')
def protected_get(verified_token: dict = Depends(check_authorization)):
    return verified_token
