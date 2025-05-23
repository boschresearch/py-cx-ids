# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import os
from uuid import uuid4
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from pycxids.core.auth.auth_factory import AuthFactory
from pycxids.ssi.w3c.jws_2020_jwt_signer import JsonWebSignature2020JWT
from pycxids.ssi.w3c.jws_2020_signer import JsonWebSignature2020
from pycxids.ssi.w3c.vc import VerifiableCredential
from pycxids.ssi.w3c.vc_hasher import JsonLdHasherCx
# debugging
from pycxids.core.jwt_decode import decode

class VcRepackageAuth(AuthFactory):
    def __init__(self, bpn: str, vp_did: str, private_key: Ed25519PrivateKey) -> None:
        """
        bpn: The one in the VC - the one we want to re-use.
        vp_did:
        """
        self.bpn = bpn
        self.vp_did = vp_did
        self.private_key = private_key

    def get_vc(self):
        """
        Return VC in case we have one on disk. Or None.
        """
        vc_fn = f"{self.bpn}.json"
        if os.path.isfile(vc_fn):
            vc_data = None
            with open(vc_fn, "rt") as f:
                vc_data = f.read()
            if vc_data:
                vc = json.loads(vc_data)
                return vc
        return None


    def get_vp(self, vcs: list, audience: str):
        jwt_vp_signer = JsonWebSignature2020JWT(key=self.private_key, did=self.vp_did)
        jwt_vp_token = jwt_vp_signer.sign_vp(vcs=vcs, audience=audience)
        return jwt_vp_token


    def get_token(self, aud: str):
        vc = self.get_vc()
        vp_token = self.get_vp(vcs=[vc], audience=aud)
        decoded = decode(vp_token, sig_to_hex=True)
        decoded_str = json.dumps(decoded, indent=4)
        with open('god_vp_token.json', 'wt') as f:
            f.write(decoded_str)
        return vp_token
