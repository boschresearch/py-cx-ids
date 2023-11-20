# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import base64
from copy import deepcopy
from pycxids.core.http_binding.crypto_utils import padding_remove
from pycxids.utils.jsonld import hash
from pycxids.ssi.w3c.signer import VcHasher
from pycxids.utils.jsonld import normalize


class JsonLdHasher(VcHasher):
    def __init__(self, header: str = None, header_b64: str = None) -> None:
        """
        header: if not given, try using the one from proof.jws
                example: '{"b64": false, "crit": ["b64"], "alg": "EdDSA"}'
        header_b64: b64 encoded (will overrule header)

        If header is not given in either way, we try getting it from the given VC.
        If it is not desired to take the header from the VC, remove the proof.jws
        """
        super().__init__()
        if header:
            self.header_b64 = padding_remove(base64.urlsafe_b64encode(header))
        self.header_b64 = header_b64

    def prepare_hashes(self, vc: dict) -> (bytes, bytes):
        unsecured_document = deepcopy(vc)
        if 'proof' in unsecured_document.keys():
            del unsecured_document['proof']

        unsecured_document_normalized = normalize(unsecured_document)
        doc_hash = hash(unsecured_document_normalized)

        proof_hash = None
        proof_options = deepcopy(vc.get('proof'))
        if proof_options:
            del proof_options['jws']
            context = vc.get('@context')
            proof_options['@context'] = context
            proof_options_normalized = normalize(proof_options)
            proof_hash = hash(proof_options_normalized)
        
        return (proof_hash, doc_hash)
    
    def prepare_jws_header(self, vc: dict) -> bytes:
        jws_origin = vc.get('proof', {}).get('jws')
        jws_header_b64 = None
        if jws_origin:
            # potentially used for verifying an existing VC
            jws_spl = jws_origin.split('.')
            jws_header_b64 = jws_spl[0]
        else:
            # potentially used for newly signing
            jws_header_b64 = self.header_b64
        return jws_header_b64.encode()

        
    def prepare_signing_input(self, vc: dict) -> bytes:
        proof_hash, doc_hash = self.prepare_hashes(vc=vc)

        overall_hash = proof_hash + doc_hash

        header_b = self.prepare_header(vc=vc)

        # assuming we use detached mode, the hash is a 'plain' hash (not b64 encoded)
        sig_input = header_b + b'.' + overall_hash
        return sig_input


class JsonLdHasherCx(JsonLdHasher):
    """
    Special Catena-X way of preparing the signing input
    Using the doc_hash (without proof_hash) is a workaround because of this issue
    https://github.com/eclipse-tractusx/SSI-agent-lib/issues/34
    also we have to b64 the payload as a workaround for:
    https://github.com/eclipse-tractusx/SSI-agent-lib/issues/43
    """
    def __init__(self, header: str = None, header_b64: str = None) -> None:
        super().__init__(header, header_b64)

    def prepare_signing_input(self, vc: dict) -> bytes:
        _, doc_hash = self.prepare_hashes(vc=vc)

        header_b = self.prepare_jws_header(vc=vc)

        doc_hash_b64 = padding_remove(base64.urlsafe_b64encode(doc_hash))
        sig_input = header_b + b'.' + doc_hash_b64
        return sig_input
