# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from pycxids.portal.api import Portal
from pycxids.portal.settings import PORTAL_OAUTH_TOKEN_ENDPOINT, PORTAL_BASE_URL, PORTAL_CLIENT_ID, PORTAL_CLIENT_SECRET

def test():
    portal = Portal(
        portal_base_url=PORTAL_BASE_URL,
        client_id=PORTAL_CLIENT_ID,
        client_secret=PORTAL_CLIENT_SECRET,
        token_url=PORTAL_OAUTH_TOKEN_ENDPOINT,
    )
    edc_endpoints = portal.discover_edc_endpoint(bpn='BPNL00000003B5MJ')

    assert len(edc_endpoints) == 1

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
