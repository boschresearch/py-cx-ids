# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
import os
import pytest
import json
from pycxids.core.http_binding.crypto_utils import padding_remove, private_key_from_seed_file
from pycxids.miw.miw import Miw
from pycxids.core.jwt_decode import decode
import base64
from pycxids.ssi.w3c.jws_2020_jwt_signer import JsonWebSignature2020JWT
from pycxids.utils.datetime import datetime_now_utc
from pycxids.utils.helper import dict_diff

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pycxids.ssi.w3c.jws_2020_signer import JsonWebSignature2020

from pycxids.ssi.w3c.vc_hasher import JsonLdHasherCx

SEED_INSECURE_FN = os.getenv('SEED_INSECURE_FN', './edc-dev-env/vault_secrets/seed.insecure')
private_key = private_key_from_seed_file(SEED_INSECURE_FN)


def test_():
    secret_fn = './.secrets/INT/consumer.miw.secret'
    secret = None
    with open(secret_fn, 'rt') as f:
        secret = f.read()
    assert secret

    tx_ssi_miw_url="https://managed-identity-wallets-new.int.demo.catena-x.net"
    tx_ssi_oauth_token_url="https://centralidp.int.demo.catena-x.net/auth/realms/CX-Central/protocol/openid-connect/token"
    tx_ssi_oauth_client_id="sa209"

    miw = Miw(base_url=tx_ssi_miw_url, client_id=tx_ssi_oauth_client_id, client_secret=secret, token_url=tx_ssi_oauth_token_url)
    credentials = miw.get_credentials()
    credentials_str = json.dumps(credentials, indent=4)
    print(credentials_str)

    # get an 'official' VC from MIW (potetnially taken from e.g. a catalog request)
    vc_miw = credentials['content'][0]

    # get BPN
    vc_miw_bpn = vc_miw.get('credentialSubject', [{}])[0].get('holderIdentifier')
    with open (f"{vc_miw_bpn}.json", "wt") as f:
        f.write(json.dumps(vc_miw, indent=4))

    # 're-package' in our own VP
    audience = 'http://localhost'
    our_did = 'did:web:miw-int.westeurope.cloudapp.azure.com:bpn0815'
    SEED_INSECURE_FN = os.getenv('SEED_INSECURE_FN', './edc-dev-env/vault_secrets/seed.insecure')
    private_key = private_key_from_seed_file(SEED_INSECURE_FN)

    jwt_vp_signer = JsonWebSignature2020JWT(key=private_key, did=our_did)
    jwt_vp_token = jwt_vp_signer.sign_vp(vcs=[vc_miw], audience=audience)

    # check whether this is detected by MIW
    verified_token = miw.verify_vp(vp=jwt_vp_token)
    assert verified_token, "Could not verify token"


if __name__ == '__main__':
    pytest.main([__file__, "-s"])
