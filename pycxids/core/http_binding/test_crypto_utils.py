# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import pytest
from pycxids.core.http_binding.crypto_utils import jwk_to_private_key_v2, key_to_private_raw, key_to_public_raw_pub, private_key_to_jwk, pub_key_to_jwk_v2, pub_key_to_jwk, generate_ed25519_key
from pycxids.core.http_binding.crypto_utils import jwk_to_pub_key, jwk_to_pub_key_v2
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

def test_pub_jwk_export_and_import():
    key: Ed25519PrivateKey = generate_ed25519_key()
    pub_key: Ed25519PublicKey = key.public_key()
    # uses jwcrypto
    export_1 = pub_key_to_jwk(pub_key=pub_key)
    # own implementation
    export_2 = pub_key_to_jwk_v2(pub_key=pub_key)
    assert export_1 == export_2, "JWK export not correct"

    import_1: Ed25519PublicKey = jwk_to_pub_key(export_1)
    import_1_pb = key_to_public_raw_pub(import_1)
    import_2: Ed25519PublicKey = jwk_to_pub_key_v2(export_1)
    import_2_pb = key_to_public_raw_pub(import_2)
    assert import_1_pb == import_2_pb, "JWK import not correct"

    private_jwk = private_key_to_jwk(key=key).export(private_key=True, as_dict=True)
    private_key_imported = jwk_to_private_key_v2(private_key_jwk=private_jwk)

    key_b = key_to_private_raw(key=key)
    key_impored_b = key_to_private_raw(key=private_key_imported)
    assert key_b == key_impored_b, "Private key export / import does not work"


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
