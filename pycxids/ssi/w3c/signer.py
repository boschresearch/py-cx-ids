# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod


class VcSigner(ABC):
    @abstractmethod
    def sign(self, data: bytes) -> bytes:
        pass
    @abstractmethod
    def prepare_proof(self, verification_method: str, proof_purpose: str = 'proofPurpose', created: str = None):
        pass
    @abstractmethod
    def sign_vc(self, vc: dict, verification_method: str, proof_purpose: str = 'proofPurpose', created: str = None):
        pass

class VcHasher(ABC):
    @abstractmethod
    def prepare_hashes(self, vc: dict) -> (bytes, bytes):
        pass
    @abstractmethod
    def prepare_signing_input(self, vc: dict) -> bytes:
        pass

class VcVerifier(ABC):
    @abstractmethod
    def verify(self, data: bytes) -> bool:
        pass
