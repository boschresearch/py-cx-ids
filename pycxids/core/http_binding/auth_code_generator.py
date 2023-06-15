# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from jwcrypto.jwk import JWKSet, JWK
from jwcrypto.jwt import JWT, JWE
# jwt lib does not support encyrption
from time import time

DEFAULT_ISS = 'http://localhost'
DEFAULT_EXP_SECONDS = 3600

def generate_auth_code(claims: dict, public_key_pem: bytes):
    """
    See jwcrypt examples for jwt encryption (jwe) with asymetric keys here:
    https://jwcrypto.readthedocs.io/en/latest/jwe.html#asymmetric-keys
    """
    if not claims.get('iss'):
        claims['iss'] = DEFAULT_ISS
    if not claims.get('exp'):
        claims['exp'] = int(time()) + DEFAULT_EXP_SECONDS
    # TODO: check 'sub' ?

    claims_str = json.dumps(claims)


    pub_key_jwk = JWK()
    pub_key_jwk.import_from_pem(data=public_key_pem)

    protected_header = {
        "alg": "RSA-OAEP-256",
        "enc": "A256CBC-HS512",
        "typ": "JWE",
        "kid":  pub_key_jwk.thumbprint(),
    }
    jwetoken = JWE(claims_str.encode(), recipient=pub_key_jwk, protected=protected_header)
    enc = jwetoken.serialize()
    return enc
