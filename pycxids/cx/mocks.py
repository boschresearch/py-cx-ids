# Copyright (c) 2024 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
import time
from uuid import uuid4
import jwt
import json
from fastapi import FastAPI, Body, Request, Header
from fastapi.middleware.gzip import GZipMiddleware

from pycxids.core.http_binding.crypto_utils import generate_ed25519_key, pub_key_to_jwk_v2
from pycxids.core.jwt_decode import decode
from pycxids.cx.mock_settings import CONSUMER_PRIVATE_KEY, CS_PRESENTATION_RESPONSE_TEMPLATE, DID_BASE, IATP_CS_BASE_URL, ISSUER_PRIVATE_KEY, MEMBERSHIP_VC_TEMPLATE, PROVIDER_PRIVATE_KEY, did_document_template

app = FastAPI(title="CX mocked services")

app.add_middleware(GZipMiddleware, minimum_size=1)

@app.get('/bdrs/bpn-directory')
def bdrs_bpn_directory():
    """
    Mocked services for

    https://github.com/eclipse-tractusx/bpn-did-resolution-service


    /bdrs -> https://bpn-did-resolution-service.int.demo.catena-x.net/api/directory
    """
    bdrs = {
        "BPNL00000003CRHK": "did:web:dim-static-prod.dis-cloud-prod.cfapps.eu10-004.hana.ondemand.com:dim-hosted:2f45795c-d6cc-4038-96c9-63cedc0cd266:holder-iatp",
        "BPNL00000007ZS71": "did:web:portal-backend.int.demo.catena-x.net:api:administration:staticdata:did:BPNL00000007ZS71",
        "BPNL00000007ZS7X": "did:web:portal-backend.int.demo.catena-x.net:api:administration:staticdata:did:BPNL00000007ZS7X",
        "BPNLprovider": "did:web:dev%3A13000:BPNLprovider",
        "BPNLconsumer": "did:web:dev%3A13000:BPNLconsumer",
        "BPNLissuer": "did:web:dev%3A13000:BPNLissuer",
    }
    return bdrs

@app.post('/portal/api/administration/connectors/discovery')
def portal_edc_discovery(body = Body(...)):
    """
    Mock the EDC Discovery service which is part of the Portal
    and returns the available EDC endpoints for a given BPN
    """
    bpn_endpoints = []
    for bpn in body:
        if bpn == 'BPNLprovider':
            bpn_endpoints.append(
                {
                    bpn: {
                        'connectorEndpoint': ['http://provider-control-plane:8282/api/v1/dsp']
                    }
                }
            )

        elif bpn == 'BPNLconsumer':
            bpn_endpoints.append(
                {
                    bpn: {
                        'connectorEndpoint': ['http://consumer-control-plane:8282/api/v1/dsp']
                    }
                }
            )

        else:
            bpn_endpoints.append(
                {
                    bpn: {
                        'connectorEndpoint': ['http://localhost']
                    }
                }
            )

    return bpn_endpoints


#####
# IATP
#####

def get_expiration_timestamp():
    return int(time.time() + 3600) # expiry is checked by EDC

def get_now_timestamp():
    return int(time.time())

def create_dummy_token(claims:dict = {}):
    # TODO: check if "sub" is needed
    if "exp" not in claims:
        claims["exp"] = get_expiration_timestamp()
    return jwt.encode(claims, 'secret', 'HS256')

def get_auth_header_payload(authorization: str):    
    print(authorization)
    auth = authorization.split(' ')[1]
    auth_jwt = decode(auth, remove_signature=True)
    return auth_jwt['payload']

def bpn_to_private_key(bpn: str):
    seed = ''
    if bpn == 'BPNLconsumer':
        seed = CONSUMER_PRIVATE_KEY
    elif bpn == 'BPNLprovider':
        seed = PROVIDER_PRIVATE_KEY
    elif bpn == 'BPNLissuer':
        seed = ISSUER_PRIVATE_KEY
    else:
        assert "Given client_id not supported."

    key = generate_ed25519_key(seed=seed)
    return key


@app.post('/sts')
def sts_get_token(body: dict = Body(...), authorization: str = Header()):
    """
    IATP:
    Creates the token that is sent with the DSP message which allows the receiver
    to fetch the actual VC/VPs from the Credential Service (CS)

    STS has 2 cases, the grantAccess case from the Consumer side and the
    signToken case from the Provider side, when the Consumer given token
    is cross-signed before it is used to query the CS
    """
    print(json.dumps(body, indent=True))
    auth_claims = get_auth_header_payload(authorization=authorization)
    client_id = auth_claims.get('client_id')
    print(f"STS client_id: {client_id}")
    assert client_id, "Please make sure client_id is set into the claims during the process. This is required to later create the correct VC/VPs."

    headers = {
        "alg": "EdDSA",
        "typ": "JWT",
        "kid": f"{DID_BASE}{client_id}#key1"
    }

    payload = {
        "exp": get_expiration_timestamp()
    }

    # grantAccess case - typically from Consumer
    if 'grantAccess' in body:
        payload['iss'] = body.get('grantAccess', {}).get('consumerDid')
        payload['aud'] = body.get('grantAccess', {}).get('providerDid')
        payload['sub'] = payload['iss']
        payload['token'] = create_dummy_token(claims={'client_id': client_id})
        payload['client_id'] = client_id # dummy service internal usage...

    # signToken case - typically the cross-signing case from the Provider
    if 'signToken' in body:
        payload['iss'] = body.get('signToken', {}).get('issuer')
        payload['aud'] = body.get('signToken', {}).get('audience')
        payload['sub'] = body.get('signToken', {}).get('subject')
        payload['token'] = body.get('signToken', {}).get('token')
        # no client_id here, since it is part of the token already and client_id here is the Provider one
    
    key = bpn_to_private_key(bpn=client_id)
    token = jwt.encode(payload, key, algorithm="EdDSA", headers=headers)

    return { "jwt": token}

@app.post('/cs/presentations/query')
def credential_service_presentations_query(body: dict = Body(), authorization: str = Header()):
    """
    IATP:
    Request contains a token that describes which VC/VPs are returned.
    """
    auth_claims = get_auth_header_payload(authorization=authorization)
    print(auth_claims)
    consumer_client_id = auth_claims.get('client_id')
    if not consumer_client_id:
        # this is the case from the Provider corss-signed token
        consumer_token = auth_claims.get('token')
        consumer_token_jwt = decode(consumer_token, verify_signature=False)
        consumer_client_id = consumer_token_jwt.get('payload', {}).get('client_id')
        assert consumer_client_id, "Could not get the client_id from the Consumer from the Provider cross-signed token content"
    assert consumer_client_id, "Please make sure client_id is set into the claims during the process. This is required to later create the correct VC/VPs."
    # create dummy Membership VC
    vc = deepcopy(MEMBERSHIP_VC_TEMPLATE)
    vc['id'] = str(uuid4())
    vc['issuanceDate'] = '2022-06-16T18:56:59Z'
    vc['expirationDate'] = '2030-06-16T18:56:59Z'
    vc['issuer'] = f"{DID_BASE}BPNLissuer"
    vc['credentialSubject']['id'] = f"{DID_BASE}{consumer_client_id}"
    vc['credentialSubject']['holderIdentifier'] = consumer_client_id
    vc['credentialSubject']['memberOf'] = ""

    jwt_vc = {
        "sub": f"{DID_BASE}{consumer_client_id}",
        #"jti": "",
        "iss": f"{DID_BASE}BPNLissuer",
        #"nbf": 0,
        #"iat": 0,
        #"exp": 0,
        #"nonce": "",
        "vc": vc
    }
    jwt_vc_header = {
        "alg": "EdDSA",
        "typ": "JWT",
        "kid": f"{jwt_vc['iss']}#key1"
    }

    issuer_key = generate_ed25519_key(seed=ISSUER_PRIVATE_KEY)
    jwt_vc_enc = jwt.encode(jwt_vc, issuer_key, algorithm="EdDSA", headers=jwt_vc_header)

    jwt_vp = {
        "iss": f"{DID_BASE}{consumer_client_id}",
        #"jti": "",
        "aud": auth_claims.get('sub'), # TODO: this is a simple dummy workaround to identify the other party from the given context!
        "nbf": get_now_timestamp(),
        "iat": get_now_timestamp(),
        "exp": get_expiration_timestamp(),
        #"nonce": "",
        "vp": {
            "@context": [
                "https://www.w3.org/2018/credentials/v1"
            ],
            "type": [
                "VerifiablePresentation"
            ],
            "verifiableCredential": [
            ]
        }
    }
    jwt_vp['vp']['verifiableCredential'] = [jwt_vc_enc]
    jwt_vp_header = {
        "alg": "EdDSA",
        "typ": "JWT",
        "kid": f"{jwt_vp['iss']}#key1"
    }

    # load key to sign VP
    key = bpn_to_private_key(bpn=consumer_client_id)
    jwt_vp_enc = jwt.encode(jwt_vp, key, algorithm="EdDSA", headers=jwt_vp_header)


    cs_response = deepcopy(CS_PRESENTATION_RESPONSE_TEMPLATE)
    cs_response['presentation'] = [jwt_vp_enc]
    print(cs_response)
    return cs_response

@app.post('/dummy/token')
def dummy_auth_token(body = Body(...)):
    """
    Returns a dummy JWT token that can be used with the other services for which
    e.g. EDC first fetches an auth token. Example STS
    For dummy purposes, we just include the client_id into the generated token's claim
    for further decision making down the 'dummy' process
    """
    params = body.split(b'&')
    client_id = ''
    for param in params:
        if param.startswith(b'client_id'):
            x = param.split(b'=')
            client_id = x[1]
    token = create_dummy_token({'client_id': client_id.decode()})
    return {"access_token": token }

@app.get('/{bpn}/did.json')
def get_did_document(bpn:str):
    """
    Return relevant dummy DID documents that is used in EDC
    """
    did_document = deepcopy(did_document_template)
    did_document['id'] = f"{DID_BASE}{bpn}"
    did_document['service'][0]['serviceEndpoint'] = IATP_CS_BASE_URL
    did_document['verificationMethod'][0]['controller'] = did_document['id']

    key = bpn_to_private_key(bpn=bpn)
    pub_key = key.public_key()

    pub_jwk = pub_key_to_jwk_v2(pub_key=pub_key)
    key_id = f"{did_document['id']}#key1"
    did_document['verificationMethod'][0]['id'] = key_id
    did_document['authentication'][0] = key_id
    did_document['verificationMethod'][0]['publicKeyJwk'] = pub_jwk

    print(json.dumps(did_document))
    return did_document


######
# catchall other calls
######
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
