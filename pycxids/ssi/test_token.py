# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import requests
import pytest
from uuid import uuid4
from pycxids.ssi.token_utils import *
from pycxids.core.http_binding.crypto_utils import *
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from jwcrypto.jwk import JWKSet, JWK


def test_token():
    # key: RSAPrivateKey = generate_rsa_key()
    # pub_key: RSAPublicKey = key.public_key()
    key: Ed25519PrivateKey = generate_ed25519_key()
    pub_key: Ed25519PublicKey = key.public_key()
    pub_jwk = pub_key_to_jwk(pub_key=pub_key)
    print(pub_jwk)

    data = {
        'hello': 'world'
    }
    token = token_create(claims=data, private_key=key)
    print(token)



if __name__ == '__main__':
    pytest.main([__file__, "-s"])
