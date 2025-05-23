# Copyright (c) 2024 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from pycxids.iatp.iatp import Sts, CredentialService
from pycxids.cx.services import BdrsDirectory
from pycxids.core.jwt_decode import decode_signed, decode
from pycxids.portal.api import Portal
from pycxids.portal.settings import PORTAL_BASE_URL, PORTAL_OAUTH_TOKEN_ENDPOINT


if __name__ == '__main__':
    secret_fn = './edc-dev-env/vault_secrets/consumer.ssi.secret'
    secret = None
    with open(secret_fn, 'rt') as f:
        secret = f.read()
    assert secret

    sts = Sts(
        base_url="https://dis-integration-service-prod.eu10.dim.cloud.sap/api/v2.0.0/iatp/catena-x-portal",
        client_id="sb-a31730da-7275-4843-99ab-e1f917297653!b464256|ica-production-dim-prod-eu10-004-prod-dis-cloud-approuter!b174292",
        client_secret=secret,
        token_url="https://bpnl00000007zs71-MatBin--GmbH--1.authentication.eu10.hana.ondemand.com/oauth/token",
        our_did="did:web:portal-backend.int.demo.catena-x.net:api:administration:staticdata:did:BPNL00000007ZS71",
        )
    # auth_header = sts.get_auth_header()
    # auth_header = auth_header.replace("Bearer ", "")
    # auth_header_decoded = decode(auth_header, remove_signature=True)
    # print(json.dumps(auth_header_decoded, indent=True))
    
    token = sts.get_sts_token(
        audience='http://localhost',
        bearer_scopes=[Sts.MEMBERSHIP_CREDENTIAL],
        provider_did="did:web:portal-backend.int.demo.catena-x.net:api:administration:staticdata:did:BPNL00000007ZS71",
    )
    token_decoded = decode(token, remove_signature=True)
    print(json.dumps(token_decoded, indent=True))

    cs = CredentialService(credential_service_base_url=CredentialService.INT_TESTING_DIM, access_token=token)
    vps = cs.get_vps()
    vps_decoded = CredentialService.decode_vps(vps=vps, verify_signatures=False)
    print(json.dumps(vps_decoded, indent=True))

    # BDRS (BPN - DID Mapping)
    #bdrs = BdrsDirectory(bdrs_base_url=BdrsDirectory.BDRS_INT, membership_vp_jwt=vps[0])
    bdrs = BdrsDirectory(bdrs_base_url="http://dev:13000/bdrs", membership_vp_jwt=vps[0])
    bpn_mappings = bdrs.get_directory()
    print(json.dumps(bpn_mappings, indent=True))

    # Find all EDC endpoints
    portal_secret = ''
    with open('.secrets/discovery.secret', 'rt') as f:
        portal_secret=f.read()
    portal = Portal(portal_base_url=PORTAL_BASE_URL, token_url=PORTAL_OAUTH_TOKEN_ENDPOINT, client_id="sa194", client_secret=portal_secret)
    bpn_details = {}
    for bpn, did in bpn_mappings.items():
        edc_endpoints = portal.discover_edc_endpoint(bpn=bpn)
        x = {
            "did": did,
            "edc_endpoints": edc_endpoints
        }
        bpn_details[bpn] = x
    bpn_details_str = json.dumps(bpn_details, indent=True)
    with open('bpn_details.json', 'wt') as f:
        f.write(bpn_details_str)
    print(bpn_details_str)