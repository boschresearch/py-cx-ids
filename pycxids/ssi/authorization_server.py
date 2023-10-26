# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from typing import Annotated
from fastapi import FastAPI, Form, Request, Header
import requests
from pycxids.core.http_binding.crypto_utils import generate_ed25519_key, private_key_to_jwk
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pycxids.ssi.token_utils import pub_key_to_jwk, jwk_to_headers
from jwcrypto.jwk import JWKSet, JWK
from jwcrypto.jwt import JWT
from pycxids.edc.settings import PROVIDER_EDC_VALIDATION_ENDPOINT

app = FastAPI()


def _init():
    """
    Return: key, pub_key, pub_jwk, pub_jwks_dict
    """
    key: Ed25519PrivateKey = generate_ed25519_key()
    pub_key: Ed25519PublicKey = key.public_key()
    pub_jwk = JWK()
    pub_jwk.import_from_pyca(pub_key)
    pub_jwk['kid'] = pub_jwk.thumbprint()
    jwks = JWKSet()
    jwks.add(pub_jwk)
    pub_jwks_dict = jwks.export(private_keys=False, as_dict=True)
    return key, pub_key, pub_jwk, pub_jwks_dict

@app.post('/token')
def token_post(request: Request,
               client_assertion_type: Annotated[str, Form()],
               client_assertion: Annotated[str, Form()],
               authorization = Header(default=None)):
    """
    Expects
    Content-Type: application/x-www-form-urlencoded
    meaning, FORM content
    client_assertion_type: urn:ietf:params:oauth:client-assertion-type:jwt-bearer
    client_assertion: contains a base64url encoded JWT
    """
    print(client_assertion)
    print(client_assertion_type)
    assert client_assertion_type == 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'

    output_claims = {'x': 'y'}

    edr_auth_code = None
    if authorization:
        spl = authorization.split(' ')
        if len(spl) == 2:
            # do we have 'Bearer ' in there in some cases?
            edr_auth_code = spl[1]
        if len(spl) == 1:
            edr_auth_code = spl[0]

    edr_details = None
    if edr_auth_code:
        r = requests.get(PROVIDER_EDC_VALIDATION_ENDPOINT, headers={'Authorization': edr_auth_code})
        if r.ok:
            edr_details = r.json().get('properties', None)
            print(json.dumps(edr_details, indent=4))
        else:
            print(f"{r.reason} - {r.content}")

    if edr_details:
        # this is for demo purposes only!
        # beware, that the edr_details were transferred encyrpted and are added to
        # an unencrypted token here!
        output_claims.update(edr_details)

    # create the access token
    headers = jwk_to_headers(sub_jwk=pub_jwk)
    kid = pub_jwk.get('kid')
    headers['kid'] = kid
    token = JWT(header=headers, claims=output_claims)
    jwk_key = private_key_to_jwk(key)
    token.make_signed_token(key=jwk_key)
    access_token = token.serialize()
    # token is NOT encrypted!
    # the client can read the content!
    return {'access_token': access_token}


@app.get('/jwks.json')
def jwks_get():
    return pub_jwks_dict


# generate new key pair on every startup
key, pub_key, pub_jwk, pub_jwks_dict = _init()
