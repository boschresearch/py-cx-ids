# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from jwcrypto.jwk import JWKSet, JWK
from jwcrypto.jwt import JWT, JWE

from pycxids.core.http_binding.auth_code_generator import generate_auth_code

def test_generate():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_key = key.public_key().public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        )
    dataset_id = '123'
    claims = {
        'dataset_id': dataset_id,
    }
    auth_code = generate_auth_code(claims=claims, public_key_pem=pub_key)
    print(auth_code)
    # TODO: test decrypting with other library
    private_key_jwk = JWK()
    private_key_jwk.import_from_pyca(key=key)
    jwetoken = JWE()
    jwetoken.deserialize(auth_code, key=private_key_jwk)
    decrypted = jwetoken.payload
    print(decrypted)
    data = json.loads(decrypted.decode())
    assert data.get('dataset_id') == dataset_id

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
