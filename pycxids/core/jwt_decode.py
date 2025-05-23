#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import jwt
import json
import sys
import os

def decode(data, verify_signature: bool = False, sig_to_hex = False, remove_signature: bool = False):
    decoded = jwt.api_jwt.decode_complete(data, options={'verify_signature': verify_signature})
    if remove_signature:
        del decoded['signature']
        return decoded

    if sig_to_hex:
        signature = decoded.get('signature')
        if isinstance(signature, bytes):
            sig_str = signature.hex()
            decoded['signature'] = sig_str

    return decoded

def decode_signed(data, pub_key, algorithms=['RS256', 'EdDSA']):
    return jwt.api_jwt.decode_complete(data, key=pub_key, algorithms=algorithms)

if __name__ == '__main__':
    args_len = len(sys.argv)
    decoded = {}
    # we don't want to depend on click library here
    if args_len == 1:
        print("Please provide at least the jwt content.")
        sys.exit()
    if args_len == 2:
        decoded = decode(data=sys.argv[1])
    if args_len == 3:
        pub_key = ''
        with open(sys.argv[2], 'r') as f:
            pub_key = f.read()
        if not pub_key:
            print(f"Could not read pub key file {sys.argv[2]}")
        decoded = decode_signed(data=sys.argv[1], pub_key=pub_key)

    #print(decoded)
    header = decoded.get('header')
    print(json.dumps(header, indent=4))
    payload = decoded.get('payload')
    print(json.dumps(payload, indent=4))