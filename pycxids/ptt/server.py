# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
import json
import base64
import base58
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Security, status, Depends, Response, Header, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidSignatureError
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from pycxids.core.settings import settings

POLICY_DIR = os.getenv('POLICY_DIR', 'policies')
if not os.path.exists:
    os.makedirs(POLICY_DIR)

POLICY_HASH = "cdfd26aaf5b1fdc6d71af7c1349869f9314b67626bc1eec44e64af674e357eed"
POLICY_HEADER = "Policy"
CERTIFICATES_DIR = 'certificates'
if not os.path.exists(CERTIFICATES_DIR):
    os.makedirs(CERTIFICATES_DIR)

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

def check_daps_signed_policy(policy_token: str = Header(..., alias='policy')):
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

def check_x509_signed_policy(policy_token: str = Header(..., alias='policy')):
    """
    We assume that the certificate hast been uploaded / registered with this server before.
    We use that previously registered x509, or more precisely its public key to verify the token signature.

    In a later step, instead of individual certificate fingerprints, we could check the certificate chain,
    which means only a few root CA certificates are uploaded / registered (AAS case in other auth mechanisms)
    """
    if not policy_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No policy given.")
    
    decoded_header = jwt.get_unverified_header(jwt=policy_token)
    print(decoded_header)
    """
    x5c = decoded_header.get('x5c')
    if not x5c:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No x5c header given in the token. Please provide the x509 certificate.")
    certificate = x509.load_pem_x509_certificate(data=x5c)
    fingerprint = certificate.fingerprint(algorithm='sha256')
    """
    fingerprint = decoded_header.get('x5t#S256')
    if not fingerprint:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No x5t#S256 token header was given in the token. It needs to contain the sha256 fingerprint of the signing certificate.")
    
    fn = os.path.join(CERTIFICATES_DIR, fingerprint)
    if not os.path.isfile(fn):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Certificate for fingerprint {fingerprint} does not exist on the server.")
    data = ''
    with open(fn, 'rb') as f:
        data = f.read()
    try:
        certificate = x509.load_pem_x509_certificate(data=data)
        public_key = certificate.public_key()
        decoded_token = jwt.decode(jwt=policy_token, key=public_key, algorithms=["RS256"], options={'verify_aud': False})

        return decoded_token.get('policy')
    except InvalidSignatureError as sigex:
        print(sigex)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Policy signature not valid.")
    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something wrong with the policy token signature.")



@app.head('/{path:path}')
def head_catch_all(path:str):
    """
    We have only 1 policy, so we use a catchall method for all HEAD requests.
    """
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

@app.get('/requiressignedpolicy')
def get_requiressignedpolicy(daps_signed_policy: str = Depends(check_daps_signed_policy)):
    """
    Checks whether the policy has been signed via consumer -> DAPS interaction
    """
    return get_signed_policy_content(signed_policy=daps_signed_policy)

@app.get('/requiresx509signedpolicy')
def get_requiresx509signedpolicy(x509_signed_policy: str = Depends(check_x509_signed_policy)):
    """
    Checks whether the policy has been signed with a x509 certificate
    """
    return get_signed_policy_content(signed_policy=x509_signed_policy)


def check_ssi_signed_policy(policy_token: str = Header(..., alias='policy')):
    if not policy_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No policy given.")

    try:    
        decoded_header = jwt.get_unverified_header(jwt=policy_token)
        print(decoded_header)
        public_key_b58 = b'JCB7SVh2bQSauqq827MzuyQPqYhqqvxvqCmUZ1DUtZqV' # TODO: fetch from ledger
        #public_key_b58 = b'JCB7SVh2bQSauqq827MzuyQPqYhqqvxvqCmUZ1DUtZqq' # wrong key for testing
        public_key_raw = base58.b58decode(public_key_b58)
        public_key = Ed25519PublicKey.from_public_bytes(public_key_raw)

        decoded = jwt.decode(jwt=policy_token, algorithms=['EdDSA'], key=public_key, verify=True)
        print(decoded)
        policy = decoded.get('policy')
        return policy
    except InvalidSignatureError as sigex:
        print(sigex)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Policy signature not valid.")
    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something wrong with the policy token signature.")


@app.get('/requiresSSIsignedpolicy')
def get_requiresSSIsignedpolicy(signed_policy: str = Depends(check_ssi_signed_policy)):
    return get_signed_policy_content(signed_policy=signed_policy)

def get_signed_policy_content(signed_policy: str):
    policy_for_this_endpoint = f"http://localhost:8080/policy/{POLICY_HASH}"
    if signed_policy != policy_for_this_endpoint:
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


@app.post('/x509upload')
def register_x509(certificate: bytes = File()):
    """
    To upload a x509 certificate (PEM) that is later used to verify the signature of signed policies.
    SECURITY: Of course this is NOT secure, since this is an upload for demo purposes only!
    """
    # TODO: security
    try:
        cert = x509.load_pem_x509_certificate(data=certificate)
        fingerprint = cert.fingerprint(algorithm=hashes.SHA256())
        # https://www.rfc-editor.org/rfc/rfc7515#section-4.1.8
        fp_encoded = base64.urlsafe_b64encode(fingerprint).rstrip(b"=").decode() # remove padding from the end
        fn = os.path.join(CERTIFICATES_DIR, fp_encoded)
        with open(fn, 'wb') as f:
            f.write(certificate)
        result = {
            'fingerprint_b64_urlsafe': fp_encoded
        }
        return result
    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something is wrong with the uploaded x509 certificate.")


if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8080')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.ptt.server:app", host=host, port=int(port), workers=int(workers), reload=False)

