# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
import json
import pyld
from dataclasses import dataclass, field
from uuid import uuid4
from pycxids.utils.datetime import datetime_now_utc
from pycxids.utils.jsonld import normalize, hash
from pycxids.ssi.w3c.signer import VcHasher, VcSigner, VcVerifier

default_context = [
    "https://www.w3.org/2018/credentials/v1",
]

VC_TYPE = 'VerifiableCredential'


@dataclass
class VerifiableCredential:
    # credential details
    id: str = str(uuid4())
    type: str = '' # this is appended to the default 'VerifiableCredential' type
    context: list = field(default_factory=list) # for e.g. new types. always appended to the default context
    issuer: str = ''
    issuance_date: str = ''
    expiration_date: str = "2024-10-01T00:00:00Z"
    subject_id: str = ''
    credential_subject: dict = field(default_factory=dict)
    # proof settings
    verification_method: str = None
    proof_purpose: str = 'proofPurpose'
    created: str = None
    # helpers
    hasher: VcHasher = None
    signer: VcSigner = None
    verifier: VcVerifier = None

    def export(self, as_dict: bool = True, with_proof: bool = True):
        vc_types = [VC_TYPE]
        if self.type:
            vc_types.append(self.type)

        context = default_context
        if self.context:
            context = context + self.context
        issuance_date_timestamp = self.issuance_date
        if not issuance_date_timestamp:
            issuance_date_timestamp = datetime_now_utc()

        cs = self.credential_subject
        try:
            if not cs.get('id'):
                cs['id'] = self.subject_id
        except:
            pass

        # TODO: fix workaround MIW
        try:
            if not cs[0].get('id'):
                cs[0]['id'] = self.subject_id
        except:
            pass

        vc = {
            '@context': context,
            'id': self.id,
            'type': vc_types,
            'issuer': self.issuer,
            'issuanceDate': issuance_date_timestamp,
            'expirationDate': self.expiration_date,
            'credentialSubject': cs,
        }
        if not with_proof:
            if as_dict:
                return vc
            else:
                return json.dumps(vc, indent=4)

        vc_with_proof = self.signer.sign_vc(
            vc=vc,
            verification_method=self.verification_method,
            proof_purpose=self.proof_purpose,
            created=self.created,
        )
        if as_dict:
            return vc_with_proof
        else:
            return json.dumps(vc_with_proof, indent=4)

    def import_(self, vc: dict):
        pass

    def sign(self, signer_func):
        pass
