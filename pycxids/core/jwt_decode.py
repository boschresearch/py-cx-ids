# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import jwt
import json
import sys
import os

def decode(data, verify_signature: bool = False):
    decoded = jwt.api_jwt.decode_complete(data, options={'verify_signature': verify_signature})
    return decoded

def decode_signed(data, pub_key):
    return jwt.api_jwt.decode_complete(data, key=pub_key, algorithms=['RS256'])

if __name__ == '__main__':
    pub_key_fn = sys.argv[1]
    data = sys.argv[2]

    if not os.path.isfile(pub_key_fn):
        print("Provide a filename with the public key as 1st param")
        sys.exit()
    if not data:
        print("Provide the jwt encoded string as 2nd param")
        sys.exit()

    pub_key = ''
    with open(pub_key_fn, 'r') as f:
        pub_key = f.read()

    decoded = decode_signed(data=data, pub_key=pub_key)
    
    print(json.dumps(decoded, indent=4))