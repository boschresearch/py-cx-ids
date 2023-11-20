# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from pycxids.core.http_binding.crypto_utils import padding_remove
from pycxids.ssi.w3c.signer import VcHasher, VcSigner
from pycxids.utils.datetime import datetime_now_utc

class JsonWebSignature2020(VcSigner):
    def __init__(self, key: Ed25519PrivateKey, hasher: VcHasher) -> None:
        self.key = key
        self.hasher = hasher

    def sign(self, data: bytes) -> bytes:
        return self.key.sign(data)

    def prepare_proof(self, verification_method: str, proof_purpose: str = 'proofPurpose', created: str = None):
        if not created:
            created = datetime_now_utc()
        proof = {
            'created': created,
            'proofPurpose': proof_purpose,
            'type': "JsonWebSignature2020",
            'verificationMethod': verification_method,
        }
        return proof

    def sign_vc(self, vc: dict, verification_method: str, proof_purpose: str = 'proofPurpose', created: str = None):
        signing_input = self.hasher.prepare_signing_input(vc=vc)
        signature = self.sign(data=signing_input)
        signature_b64 = padding_remove(base64.urlsafe_b64encode(signature))
        jws_header = signing_input.split(b'.')[0]
        jws = f"{jws_header.decode()}..{signature_b64.decode()}"
        proof = self.prepare_proof(verification_method=verification_method, proof_purpose=proof_purpose, created=created)
        proof['jws'] = jws
        vc['proof'] = proof
        return vc
        
