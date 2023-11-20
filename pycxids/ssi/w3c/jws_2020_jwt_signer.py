# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


import base64
import json
import time
from uuid import uuid4
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from pycxids.core.http_binding.crypto_utils import padding_remove
from pycxids.ssi.w3c.signer import VcHasher, VcSigner
from pycxids.utils.datetime import datetime_now_utc
from datetime import datetime

class JsonWebSignature2020JWT(VcSigner):
    def __init__(self, key: Ed25519PrivateKey, did: str) -> None:
        """
        For creating a VP in JWT
        did: The DID
        """
        self.key = key
        self.did = did

    def sign(self, data: bytes) -> bytes:
        return self.key.sign(data)

    def prepare_proof(self, verification_method: str, proof_purpose: str = 'proofPurpose', created: str = None):
        pass

    def sign_vc(self, vc: dict, verification_method: str, proof_purpose: str = 'proofPurpose', created: str = None):
        pass

    def sign_vp(self, vcs: list, audience: str):
        vp = {
            'id': self.did + str(uuid4()),
            'proof': None,
            'type': [
                'VerifiablePresentation'
            ],
            '@context': [
                'https://www.w3.org/2018/credentials/v1'
            ],
            'verifiableCredential': vcs,
        }
        jwt_header = {
            'kid': self.did,
            'typ': 'JWT',
            'alg': 'EdDSA',
        }
        now_sec = int(datetime.utcnow().timestamp())
        jwt_payload = {
            'sub': self.did,
            'aud': audience,
            'iss': self.did,
            'exp': now_sec + 3600 * 24,
            #'iat': now_sec, # not used in MIW right now
            'jti': str(uuid4()),
            'vp': vp,
        }

        jwt_header_str = json.dumps(jwt_header) # we don't care for serialization, separator, etc...
        jwt_header_b64 = padding_remove(base64.urlsafe_b64encode(jwt_header_str.encode()))

        jwt_payload_str = json.dumps(jwt_payload)
        jwt_payload_b64 = padding_remove(base64.urlsafe_b64encode(jwt_payload_str.encode()))

        # since we're not in detached mode, also the payload is b64 encoded!
        signing_input = jwt_header_b64 + b'.' + jwt_payload_b64
        signature = self.sign(data=signing_input)
        signature_b64 = padding_remove(base64.urlsafe_b64encode(signature))

        jwt = f"{signing_input.decode()}.{signature_b64.decode()}"
        return jwt


