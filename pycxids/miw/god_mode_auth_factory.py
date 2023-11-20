# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from uuid import uuid4
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from pycxids.core.auth.auth_factory import AuthFactory
from pycxids.ssi.w3c.jws_2020_jwt_signer import JsonWebSignature2020JWT
from pycxids.ssi.w3c.jws_2020_signer import JsonWebSignature2020
from pycxids.ssi.w3c.vc import VerifiableCredential
from pycxids.ssi.w3c.vc_hasher import JsonLdHasherCx
# debugging
from pycxids.core.jwt_decode import decode

class GodModeAuth(AuthFactory):
    def __init__(self, bpn: str, issuer_bpn: str, our_did_prefix: str, their_did_prefix: str, private_key: Ed25519PrivateKey, header_b64: str = "eyJhbGciOiJFZERTQSJ9") -> None:
        """
        bpn: example: BPNL00000003B5MJ
        issuer_bpn: example: BPNL00000003CRHK
        our_did_prefix: example: did:web:miw-int.westeurope.cloudapp.azure.com
        their_did_prefix: example: did:web:managed-identity-wallets-new.int.demo.catena-x.net
        """
        self.bpn = bpn
        self.issuer_bpn = issuer_bpn
        self.our_did_prefix = our_did_prefix
        self.their_did_prefix = their_did_prefix
        self.private_key = private_key
        self.header_b64 = header_b64

    def get_vc(self):
        cx_hasher = JsonLdHasherCx(header_b64=self.header_b64)
        signer = JsonWebSignature2020(self.private_key, hasher=cx_hasher)

        vc = VerifiableCredential(
            id=f"{self.their_did_prefix}:{self.issuer_bpn}#" + str(uuid4()),
            issuer=f"{self.their_did_prefix}:{self.issuer_bpn}",
            subject_id=f"{self.their_did_prefix}:{self.bpn}",
            type="SummaryCredential",
            context=[
                "https://catenax-ng.github.io/product-core-schemas/SummaryVC.json",
                "https://w3id.org/security/suites/jws-2020/v1"
            ],
            credential_subject=[
            {
                "contractTemplate": "https://public.catena-x.org/contracts/",
                "holderIdentifier": self.bpn,
                #"id": f"{self.their_did_prefix}:{self.bpn}", # EDC check
                "id": f"{self.our_did_prefix}:{self.bpn}",
                "items": [
                    "BpnCredential",
                    "MembershipCredential"
                ],
                "type": "SummaryCredential" # MIW: why is this here? no clue!
            }], # MIW: why is this an array?
            verification_method=f"{self.our_did_prefix}:{self.issuer_bpn}#", # our DID server
            hasher=cx_hasher,
            signer=signer,
        )
        vc_signed = vc.export(as_dict=True, with_proof=True)
        with open('god_mode_vc_signed.json', 'wt') as f:
            f.write(json.dumps(vc_signed, indent=4))
        return vc_signed


    def get_vp(self, vcs: list, audience: str):
        jwt_vp_signer = JsonWebSignature2020JWT(key=self.private_key, did=f"{self.our_did_prefix}:{self.bpn}")
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
