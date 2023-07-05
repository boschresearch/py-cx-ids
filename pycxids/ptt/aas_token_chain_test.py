# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import time
from datetime import datetime
import json
import uuid
import base64
import requests
import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from OpenSSL import crypto

TOKEN_FN = os.getenv('TOKEN_FN', './.secrets/i40/token_with_x509_chain.txt')

token = ''
with open(TOKEN_FN, 'rb') as f:
    token = f.read()

token_header = jwt.get_unverified_header(token)

x5c = token_header.get('x5c')

print(f"number of certs: {len(x5c)}")
# should be DER encoded certificate
data1 = x5c[0]

data1_b64_decoded = base64.b64decode(data1.encode())

certificate = x509.load_der_x509_certificate(data1_b64_decoded)
subject = certificate.subject
print(subject)

# text output not available in cryptography package, but in pyopenssl
crypto_cert = crypto.X509.from_cryptography(crypto_cert=certificate)
crt_txt = crypto.dump_certificate(type=crypto.FILETYPE_TEXT, cert=crypto_cert)

with open('test_cert_out.txt', 'wb') as f:
    f.write(crt_txt)
