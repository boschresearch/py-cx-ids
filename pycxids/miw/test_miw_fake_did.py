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
from pycxids.utils.datetime import datetime_now_utc
from pycxids.utils.helper import dict_diff

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pycxids.ssi.w3c.jws_2020_signer import JsonWebSignature2020

from pycxids.ssi.w3c.vc_hasher import JsonLdHasherCx

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
    #bearer_token = miw.get_auth_header()
    #print(bearer_token)
    credentials = miw.get_credentials()
    credentials_str = json.dumps(credentials, indent=4)
    print(credentials_str)
    vc_miw = credentials['content'][0]
    our_vc = deepcopy(vc_miw)
    del our_vc['proof']
    proof = deepcopy(vc_miw.get('proof'))

    jws = proof.get('jws')
    header_b64 = jws.split('.')[0]
    cx_hasher = JsonLdHasherCx(header_b64=header_b64)
    signing_input = cx_hasher.prepare_signing_input(our_vc)
    signer = JsonWebSignature2020(private_key, hasher=cx_hasher)
    signature = signer.sign(signing_input)
    signature_b64 = padding_remove(base64.urlsafe_b64encode(signature))
    new_jws = f"{header_b64}..{signature_b64.decode()}"
    print(new_jws)
    now = datetime_now_utc()
    new_proof = {
        'created': now,
        'jws': new_jws,
        'proofPurpose': 'proofPuspose',
        'type': 'JsonWebSignature2020',
        'verificationMethod': 'did:web:miw-int.westeurope.cloudapp.azure.com:BPNL00000003CRHK#'
    }
    new_vc = deepcopy(our_vc)
    new_vc['proof'] = new_proof

    #new_vc['issuer'] = 'XXX'


    vp = miw.create_presentation(verifiable_credential=new_vc, aud='http://localhost')
    assert vp, "Could not create VP"
    print(json.dumps(vp))
    verified = miw.verify_vp(vp=vp)
    assert verified['valid'], "Could not verify VP"
    decoded = decode(vp)
    decoded['signature'] = decoded['signature'].hex()
    decoded_vp_str = json.dumps(decoded, indent=4)
    with open('decoded_vp.json', 'wt') as f:
        f.write(decoded_vp_str)

    #vc['proof']['created'] = '2029-07-10T00:34:01Z' # changed
    vc['proof']['verificationMethod'] = 'did:web:miw-int.westeurope.cloudapp.azure.com:BPNL00000003CRHK#' # changed
    vp = miw.create_presentation(verifiable_credential=vc, aud='http://localhost')
    assert vp, "Could not create VP"
    print(json.dumps(vp))
    verified = miw.verify_vp(vp=vp)
    # MIW should NOT mark this valid, but does
    # https://github.com/eclipse-tractusx/SSI-agent-lib/issues/34
    assert verified['valid'] == False, "Changed proof options still produced a valid verified flag"

    vc['credentialSubject'][0]['holderIdentifier'] = 'xyz' # changed
    vp = miw.create_presentation(verifiable_credential=vc, aud='http://localhost')
    assert vp, "Could not create VP"
    print(json.dumps(vp))
    verified = miw.verify_vp(vp=vp)
    assert verified['valid'] == False, "Updated VC claims did not fail signature verification"



if __name__ == '__main__':
    pytest.main([__file__, "-s"])
