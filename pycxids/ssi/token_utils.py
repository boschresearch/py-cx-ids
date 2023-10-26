# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from typing import Union
import jwt
from jwcrypto.jwk import JWK, JWKOperationsRegistry
import base58
from pycxids.core.http_binding.crypto_utils import key_to_public_raw
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from pycxids.core.http_binding.crypto_utils import pub_key_to_jwk, pub_key_to_jwk_thumbprint

from uuid import uuid4

# https://openid.github.io/SIOPv2/openid-connect-self-issued-v2-wg-draft.html#name-self-issued-id-token
# https://datatracker.ietf.org/doc/html/rfc9278
SIOP_V2_JWK_THUMBPRINT_PREFIX = 'urn:ietf:params:oauth:jwk-thumbprint:sha-256:'

def jwk_to_headers(sub_jwk):
    if sub_jwk['kty'] == 'OKP':
        return {
            'alg': 'EdDSA',
            'crv': sub_jwk['crv']
        }
    if sub_jwk['kty'] == 'RSA':
        return {
            'alg': 'RS256'
        }


def token_create(claims: dict, private_key: Union[RSAPrivateKey, Ed25519PrivateKey], kid: str = ''):
    """
    kid: can be a DID. reciever needs to know how to resolve pub key from it
    claims:
    private_key_fn: ed25519
    """
    pub_key = private_key.public_key()
    sub_jwk = pub_key_to_jwk(pub_key=pub_key)
    sub_jwk_thumbprint = pub_key_to_jwk_thumbprint(pub_key=pub_key)

    # contains our 'local' identity key
    # https://openid.github.io/SIOPv2/openid-connect-self-issued-v2-wg-draft.html#name-self-issued-id-token
    claims['sub_jwk'] = sub_jwk

    jwt_headers = jwk_to_headers(sub_jwk=sub_jwk)
    jwt_headers['kid'] = SIOP_V2_JWK_THUMBPRINT_PREFIX + sub_jwk_thumbprint
    token = jwt.encode(claims, key=private_key, headers=jwt_headers, algorithm=jwt_headers['alg'])

    return token

def token_decode(token: bytes, get_pub_key_fc) -> dict:
    """
    token to claims dict
    get_pub_key_fc: function to receive the kid as param and expect a public_key_58 bytes
    """
    decoded_header = jwt.get_unverified_header(jwt=token)
    #print(decoded_header)
    kid:str = decoded_header.get('kid')
    if kid.startswith(SIOP_V2_JWK_THUMBPRINT_PREFIX):
        # extract without verifying first to get the sub_jwk with the public key
        decoded_unverified = jwt.decode(jwt=token, algorithms=['EdDSA', 'RS256'], key=public_key, verify=False)
        jwk = JWK()
        jwk.import_key(decoded_unverified.get('sub_jwk'))
        input_jwk_thumbprint_uri = jwk.thumbprint_uri
        if input_jwk_thumbprint_uri != kid:
            raise Exception("kid does not match thumbprint of the sub_jwk claim")
        pub_key = jwk.get_op_key(operation='verify')
        print(pub_key)
    
    public_key_b58 = get_pub_key_fc(kid)
    
    public_key_raw = base58.b58decode(public_key_b58)
    public_key = Ed25519PublicKey.from_public_bytes(public_key_raw)

    decoded = jwt.decode(jwt=token, algorithms=['EdDSA', 'RS256'], key=public_key, verify=True)
    print(decoded)
    return decoded



