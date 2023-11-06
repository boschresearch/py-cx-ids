# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import base64
from copy import deepcopy
import json
import pytest
from pycxids.core.http_binding.crypto_utils import jwk_to_pub_key_v2, padding_add, padding_remove
from pycxids.utils.jsonld import normalize, hash
from multiformats.multibase import decode_raw, encode as multibase_encode
from multiformats import multicodec
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def test_vc():
    """
    Test test suite VC
    """
    data = ''

    with open('./pycxids/ssi/w3c/tests/test_data/jws_test_suite/key-0-ed25519.json', 'rt') as f:
        data = f.read()
    key_data = json.loads(data)
    pub_key_jwk = key_data.get('publicKeyJwk', {})

    pub_key = jwk_to_pub_key_v2(pub_jwk=pub_key_jwk)


    with open('./pycxids/ssi/w3c/tests/test_data/jws_test_suite/afgo_vc0.json', 'rt') as f:
        data = f.read()
    vc = json.loads(data)

    unsecured_document = deepcopy(vc)
    del unsecured_document['proof']

    proof_options = deepcopy(vc['proof'])
    del proof_options['jws']
    context = vc.get('@context')
    proof_options['@context'] = context

    unsecured_document_normalized = normalize(unsecured_document)
    doc_hash = hash(unsecured_document_normalized)
    print(f"doc_hash (hex): {doc_hash.hex()}")

    proof_options_normalized = normalize(proof_options)
    proof_hash = hash(proof_options_normalized)
    print(f"proof_hash (hex): {proof_hash.hex()}")

    overall_hash = proof_hash + doc_hash
    print(f"overall_hash (hex): {overall_hash.hex()}")

    print(len(proof_hash))
    print(len(doc_hash))
    print(len(overall_hash))

    jws_origin = vc['proof']['jws']
    print(jws_origin)

    jws_spl = jws_origin.split('.')
    jws_sig_b64 = jws_spl[-1]
    print(jws_sig_b64)
    jws_sig = base64.urlsafe_b64decode(padding_add(jws_sig_b64))

    jws_header_b64 = jws_spl[0]
    jws_header = base64.urlsafe_b64decode(padding_add(jws_header_b64))
    print(jws_header)

    # in detached mode, the payload is NOT b64 encoded!
    sig_input = jws_header_b64.encode() + b'.' + overall_hash
    sig_input_wrong = sig_input + b'x'

    try:
        pub_key.verify(signature=jws_sig, data=sig_input)
    except Exception as ex:
        print(ex)
        assert False, "Could not verify signature."

    try:
        pub_key.verify(signature=jws_sig, data=sig_input_wrong)
        assert False, "Verified signature with wrong input."
    except Exception as ex:
        print(ex)

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
