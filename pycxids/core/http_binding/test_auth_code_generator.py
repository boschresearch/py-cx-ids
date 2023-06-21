# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import pytest
from pycxids.core.http_binding.auth_code_generator import generate_auth_code
from pycxids.core.http_binding.crypto_utils import decrypt, verify, generate_rsa_key, key_to_public_pem, key_to_private_pkcs8

def test_generate():
    encryption_key = generate_rsa_key()
    encryption_pub_key = key_to_public_pem(key=encryption_key)
    encryption_private_key = key_to_private_pkcs8(key=encryption_key)

    signing_key = generate_rsa_key()
    signing_pub_key = key_to_public_pem(key=signing_key)
    signing_private_key = key_to_private_pkcs8(key=signing_key)
    dataset_id = '123'
    claims = {
        'dataset_id': dataset_id,
    }
    auth_code = generate_auth_code(claims=claims, encryption_public_key_pem=encryption_pub_key, signing_private_key_pem=signing_private_key)
    print(auth_code)
    # TODO: test decrypting with other library
    decrypted = decrypt(payload=auth_code, private_key_pem=encryption_private_key)
    print(decrypted)
    verified_payload = verify(payload=decrypted, public_key_pem=signing_pub_key)
    print(verified_payload)
    j = json.loads(verified_payload.decode())
    assert j.get('dataset_id') == dataset_id, "Could not verify content"


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
