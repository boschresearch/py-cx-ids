# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import pytest
import requests
from pycxids.edc.settings import CONSUMER_IDS_ENDPOINT


def test():
    token_fn = 'pycxids/core/http_binding/examples/ssi_auth_header_entire_field_b64.txt'
    token = ''
    with open(token_fn, 'rt') as f:
        token = f.read()
    
    r = requests.post(f"{CONSUMER_IDS_ENDPOINT}/catalog/request", headers={'authorization': token})
    assert r.status_code == 401, "Access must not be allowed with this token and must return a 401 Unauthorized"
    print(r.content)

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
