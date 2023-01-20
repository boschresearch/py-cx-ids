import os
from json import JSONDecodeError
from uuid import uuid4
from typing import Optional
from fastapi import FastAPI, Request, Form
from jwcrypto.jwk import JWKSet, JWK
from jwcrypto.jwt import JWT
import jwt
from datetime import datetime, timedelta


app = FastAPI(title="DAPS Mock")

DAPS_CERT_FN = os.getenv('DAPS_CERT_FN', './daps.crt')
DAPS_PRIVATE_KEY_FN = os.getenv('DAPS_PRIVATE_KEY_FN', './daps.key')


@app.get('/.well-known/jwks.json')
def get_jwks():
    daps_crt = None
    with open(DAPS_CERT_FN, 'rb') as f:
        daps_crt = f.read()
    daps_jwk = JWK()
    daps_jwk.import_from_pem(data=daps_crt)
    jwks = JWKSet()
    jwks.add(daps_jwk)
    result = jwks.export(private_keys=False, as_dict=True)
    return result

@app.post('/token')
async def post_token(
    request: Request,
    client_assertion: Optional[str] = Form(None),
    resource: Optional[str] = Form(None)
    ):
    """
    WARNING: This basically 'signs' everything it gets! Never use this in production environment.
    This is purely a 'mock' version of the DAPS for local development!

    The required field 'client_assertion' can be part of query_params OR it is a FORM field.
    First check for the FORM field.

    """
    if not client_assertion:
        params = request.query_params
        #print(params)
        # TODO: security: we don't check the client signature yet!!!
        client_assertion = params.get('client_assertion', '')
    decoded = jwt.decode(jwt=client_assertion, options={'verify_signature': False})

    if not resource:
        params = request.query_params
        resource = params.get('resource', '')

    # preparte private key
    private_key = JWK()
    private_key_content = None
    with open(DAPS_PRIVATE_KEY_FN, 'rb') as f:
        private_key_content = f.read()
    private_key.import_from_pem(data=private_key_content)

    now = datetime.now()
    header = {
        "kid": private_key.key_id,
        "typ": "at+jwt",
        "alg": "RS256"
    }
    payload = {
        "scope": "idsc:IDS_CONNECTOR_ATTRIBUTES_ALL",
        "iss": "http://daps-mock",
        "sub": decoded['sub'],
        "aud": [
            #decoded['aud']
            resource
        ],
        "jti": str(uuid4()),
        "client_id": decoded['sub'],

        "exp" : int((now + timedelta(minutes=10)).timestamp()),
        "nbf": int(now.timestamp()),
        "iat": int(now.timestamp()),
        "@type": "ids:DatPayload",
        "@context": "https://w3id.org/idsa/contexts/context.jsonld",
        "securityProfile": "idsc:BASIC_SECURITY_PROFILE",
        "referringConnector": "", # TODO: this is used to parse out the BPN in some cases
    }
    token = JWT(header=header, claims=payload)
    #print(token)

    token.make_signed_token(key=private_key)
    print(token)
    token_envelope = {
        "access_token": token.serialize(),
    }

    return token_envelope


if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8000')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("main:app", host=host, port=int(port), workers=int(workers), reload=False)
