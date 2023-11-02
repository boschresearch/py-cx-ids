# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import pytest
import json
from pycxids.miw.miw import Miw
from pycxids.core.jwt_decode import decode
import base64


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
    vc = credentials['content'][0]
    vp = miw.create_presentation(verifiable_credential=vc, aud='http://localhost')
    assert vp, "Could not create VP"
    print(json.dumps(vp))
    verified = miw.verify_vp(vp=vp)
    assert verified['valid'], "Could not verify VP"
    # decoded = decode(vp)
    # decoded['signature'] = ''
    # print(json.dumps(decoded, indent=4))

    vc['proof']['created'] = '2029-07-10T00:34:01Z' # changed
    #vc['proof']['verificationMethod'] = 'did:web:xxx-managed-identity-wallets-new.int.demo.catena-x.net:BPNL00000003CRHK#' # changed
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
