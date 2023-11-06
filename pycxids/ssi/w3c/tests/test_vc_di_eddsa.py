# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import pytest
from pycxids.utils.jsonld import normalize, hash
from multiformats.multibase import decode_raw, encode as multibase_encode
from multiformats import multicodec
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

def test_vc():
    """
    Use the test vector example to double check what we're doing is correct
    https://www.w3.org/TR/vc-di-eddsa/#test-vectors
    """
    data = ''

    with open('./pycxids/ssi/w3c/tests/test_data/vc-di-eddsa/example-7.json', 'rt') as f:
        data = f.read()
    key_data = json.loads(data)
    key_data_private = key_data.get('privateKeyMultibase')
    l = len(key_data_private)
    print(l)
    mb, private_key_b = decode_raw(key_data_private)
    print(mb)
    l2 = len(private_key_b)
    print(l2)
    codec, private_bytes = multicodec.unwrap(private_key_b)
    print(codec)
    l6 = len(private_bytes)
    print(l6)
    key: Ed25519PrivateKey = Ed25519PrivateKey.from_private_bytes(private_bytes)


    with open('./pycxids/ssi/w3c/tests/test_data/vc-di-eddsa/example-8.json', 'rt') as f:
        data = f.read()
    unsecured_document = json.loads(data)

    with open('./pycxids/ssi/w3c/tests/test_data/vc-di-eddsa/example-11.json', 'rt') as f:
        data = f.read()
    proof_options = json.loads(data)

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

    sig = key.sign(overall_hash)
    sig_hex = sig.hex()
    print(f"signature: {sig_hex}")
    # https://www.w3.org/TR/vc-di-eddsa/#example-signature-of-combined-hashes-hex
    given_sig_hex = "3237ba3b695c09e199540507ead17a58300cc4efe91ce19d582ad7e001455190f1ea3d13bdeff2cbaf7f30da7fe9f24b475511ef3875b6efe7cc9f49d3f55b02"
    assert given_sig_hex == sig_hex, "Something went wrong with signing. Signature differs from given signature."

    # https://www.w3.org/TR/vc-di-eddsa/#example-signature-of-combined-hashes-base58-btc
    given_sig_b58btc = "z21EVs3eXERqTn4acNHT9viboqgzUaQ3kTmhPT3eA8qrVPE7CrQq78WkzctnMX5W4CrzcKnHw8V6dvy5pgWYCU5e9"
    sig_b58_mb = multibase_encode(data=sig, base='base58btc')
    assert given_sig_b58btc == sig_b58_mb, "Multibase sig differs from given sig."

    # also test the verify step from the pub_key
    pub_key: Ed25519PublicKey = key.public_key()
    try:
        pub_key.verify(signature=sig, data=overall_hash)
    except Exception as ex:
        print(ex)
        assert False, "Could not verify signature"

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
