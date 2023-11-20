# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
import os
from uuid import uuid4
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
from pycxids.ssi.w3c.vc import VerifiableCredential
from pycxids.ssi.w3c.vc_hasher import JsonLdHasherCx
from pycxids.miw.god_mode_auth_factory import GodModeAuth

SEED_INSECURE_FN = os.getenv('SEED_INSECURE_FN', './edc-dev-env/vault_secrets/seed.insecure')
private_key = private_key_from_seed_file(SEED_INSECURE_FN)


def test_():
    secret_fn = './.secrets/INT/provider.miw.secret'
    secret = None
    with open(secret_fn, 'rt') as f:
        secret = f.read()
    assert secret
    # TODO: get from settings

    tx_ssi_miw_url="https://managed-identity-wallets-new.int.demo.catena-x.net"
    tx_ssi_oauth_token_url="https://centralidp.int.demo.catena-x.net/auth/realms/CX-Central/protocol/openid-connect/token"
    tx_ssi_oauth_client_id="sa209"

    miw = Miw(base_url=tx_ssi_miw_url, client_id=tx_ssi_oauth_client_id, client_secret=secret, token_url=tx_ssi_oauth_token_url)

    god = GodModeAuth(
        bpn="BPNL00000003B5MJ",
        issuer_bpn="BPNL00000003CRHK",
        our_did_prefix="did:web:miw-int.westeurope.cloudapp.azure.com",
        their_did_prefix="did:web:managed-identity-wallets-new.int.demo.catena-x.net",
        private_key=private_key,
        )

    # now create our own VP
    jwt_vp_token = god.get_token(aud='http://localhost')
    verified_our_vp = miw.verify_vp(vp=jwt_vp_token)
    assert verified_our_vp['valid'], "Could not verify VP"



if __name__ == '__main__':
    pytest.main([__file__, "-s"])
