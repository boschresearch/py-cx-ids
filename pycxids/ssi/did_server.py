# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
import json
import os
import base58
from typing import Annotated
from fastapi import FastAPI, Form, Request

from pydid import DID, DIDDocument, VerificationMethod

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pycxids.core.http_binding.crypto_utils import private_key_from_seed_file, pub_key_to_jwk_v2

# private key for DID document
SEED_INSECURE_FN = os.getenv('SEED_INSECURE_FN', './edc-dev-env/vault_secrets/seed.insecure')
private_key = private_key_from_seed_file(SEED_INSECURE_FN)
pub_key: Ed25519PublicKey = private_key.public_key()

pub_key_jwk = pub_key_to_jwk_v2(pub_key=pub_key)

app = FastAPI()

did_document_origin = {
  "id": "did:web:managed-identity-wallets-new.int.demo.catena-x.net:BPNL00000003CRHK",
  "verificationMethod": [
    {
      "controller": "did:web:managed-identity-wallets-new.int.demo.catena-x.net:BPNL00000003CRHK",
      "id": "did:web:managed-identity-wallets-new.int.demo.catena-x.net:BPNL00000003CRHK#",
      "publicKeyJwk": {
        "crv": "Ed25519",
        "kty": "OKP",
        "x": "ExIKmgRdR5RU31awiDL8f--vZisDkCwZTHUEXXRN2xE"
      },
      "type": "JsonWebKey2020"
    }
  ],
  "@context": [
    "https://www.w3.org/ns/did/v1"
  ]
}

did_document = {
  "id": "",
  "verificationMethod": [
    {
      "controller": "",
      "id": "",
      "publicKeyJwk": pub_key_jwk,
      "type": "JsonWebKey2020"
    }
  ],
  "@context": [
    "https://www.w3.org/ns/did/v1"
  ]
}

@app.get('/{bpn:path}/did.json')
def did_document_get(bpn: str):
    """
    """
    print('did')
    print(f"bpn: {bpn}")
    id = f"did:web:miw-int.westeurope.cloudapp.azure.com:{bpn}"
    controller = id
    key_id = f"{id}#"
    doc = deepcopy(did_document)
    doc['id'] = id
    doc['verificationMethod'][0]['controller'] = controller
    doc['verificationMethod'][0]['id'] = key_id
    print(json.dumps(doc, indent=4))

    return doc
