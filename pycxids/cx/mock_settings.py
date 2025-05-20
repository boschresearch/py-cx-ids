# Copyright (c) 2025 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os

from pycxids.core.http_binding.crypto_utils import generate_seed

ISSUER_PRIVATE_KEY = os.getenv('ISSUER_PRIVATE_KEY', generate_seed())
CONSUMER_PRIVATE_KEY = os.getenv('CONSUMER_PRIVATE_KEY', generate_seed())
PROVIDER_PRIVATE_KEY = os.getenv('PROVIDER_PRIVATE_KEY', generate_seed())

DID_BASE = os.getenv('DID_BASE', 'did:web:dev%3A13000:')
IATP_CS_BASE_URL = os.getenv('IATP_CS_BASE_URL', 'http://dev:13000/cs')

# https://catenax-ev.github.io/docs/next/standards/CX-0149-Dataspaceidentityandidentification#2211-membership-credential
MEMBERSHIP_VC_TEMPLATE = {
  "id": "uuid",
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://w3id.org/catenax/credentials/v1.0.0"
  ],
  "type": ["VerifiableCredential", "MembershipCredential"],
  "issuanceDate": "{creation date - format: 2022-06-16T18:56:59Z}",
  "expirationDate": "{expiration date - format: 2022-06-16T18:56:59Z}",
  "issuer": "{did issuer}",
  "credentialSubject": {
    "id": "{did holder}",
    "holderIdentifier": "{bpn}",
    "memberOf": "{membership level}"
  }
}

CS_PRESENTATION_RESPONSE_TEMPLATE = {
  #"@context": ["https://w3id.org/dspace-dcp/v1.0/dcp.jsonld"],
  "@context": ["https://w3id.org/tractusx-trust/v0.8"],
  "type": "PresentationResponseMessage",
  "presentation": [] # those are the JWT ecoded VPs?!
}

did_document_template = {
    "id": "",
    "service": [
      {
        "id": "dim:web:xxx",
        "type": "CredentialService",
        "serviceEndpoint": ""
      }
    ],
    "@context": [
      "https://www.w3.org/ns/did/v1"
    ],
    "keyAgreement": [],
    "authentication": [
      "key1"
    ],
    "assertionMethod": [],
    "verificationMethod": [
      {
        "id": "key1",
        "type": "JsonWebKey2020",
        "controller": "",
        "publicKeyJwk": {
          "x": "",
          "y": "",
          "crv": "secp256k1",
          "kty": "EC"
        }
      }
    ]
  }