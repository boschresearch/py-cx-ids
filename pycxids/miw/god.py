# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


import json
from pycxids.miw.god_mode_helper import god_mode_fetch

#COFINITY_PREPROD_BPN_ISSUER = 'BPNL000000000000'
COFINITY_PREPROD_BPN_ISSUER = 'BPNL00000003CRHK'
#COFINITY_PREPROD_THEIR_DID_PREFIX = "did:web:managed-identity-wallet.preprod.cofinity-x.com"
COFINITY_PREPROD_THEIR_DID_PREFIX = "did:web:managed-identity-wallets-new.int.demo.catena-x.net"

# asset_id = 'binzer-test-2'
# provider_ids_endpoint = 'https://controlplane.preprod.cofinity-x.com/api/v1/dsp'
# bpn = 'BPNL000000000LQV'
# #bpn = 'BPNL000000000XXX'

# BMW Cofinity PREPROD
# asset_id = 'urn:uuid:a9189c22-7a4f-4afa-b94c-423e57b29357-urn:uuid:2b9c8afc-a1c7-4dd5-8b31-8aa8f1a61fa2'
# provider_ids_endpoint = 'https://connector-trace-int.edc.aws.bmw.cloud'
# bpn = 'BPNL00000000015G'


# BMW Catena INT
# asset_id = ''
# provider_ids_endpoint = 'https://connector-release.edc.aws.bmw.cloud'
# # no BPN access policies

"""
https://managed-identity-wallet.preprod.cofinity-x.com
https://centralidp.preprod.cofinity-x.com/auth/realms/CX-Central/protocol/openid-connect/token
Operator/Issuer: BPNL000000000000

https://bpdm0.cofinity-preprod.cx.api.mercedes-benz.com/api/v1/dsp
"""

# Bosch Catena INT
# asset_id = ''
# provider_ids_endpoint = 'https://edc-1-1.qa.catenax.bosch.tech/api/v1/dsp'
# bpn = 'BPNvip'

# local dev
asset_id = ''
provider_ids_endpoint = 'http://provider-control-plane:8282/api/v1/dsp'
bpn = 'BPNvip'

data = god_mode_fetch(asset_id=asset_id, bpn=bpn, provider_ids_endpoint=provider_ids_endpoint,
                      issuer_bpn=COFINITY_PREPROD_BPN_ISSUER, their_did_prefix=COFINITY_PREPROD_THEIR_DID_PREFIX)
assert data
data_str = ''
try:
    data_str = json.dumps(data, indent=4)
except:
    data_str = data

print(data_str)
with open('god_result.json', 'wt') as f:
    f.write(data_str)
