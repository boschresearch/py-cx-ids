# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from time import time
from pycxids.core.http_binding.crypto_utils import *

DEFAULT_ISS = 'http://localhost'
DEFAULT_EXP_SECONDS = 3600

def generate_auth_code(claims: dict, encryption_public_key_pem: bytes, signing_private_key_pem: bytes):
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

    signed_message = sign(payload=claims_str.encode(), private_key_pem=signing_private_key_pem)
    encrypted_message = encrypt(payload=signed_message, public_key_pem=encryption_public_key_pem)
    return encrypted_message
