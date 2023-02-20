# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os

PROVIDER_EDC_BASE_URL = os.getenv('PROVIDER_EDC_BASE_URL', 'http://provider-control-plane:9193/api/v1/data')
assert PROVIDER_EDC_BASE_URL

PROVIDER_EDC_API_KEY = os.getenv('PROVIDER_EDC_API_KEY', 'dontuseinpublic')
assert PROVIDER_EDC_API_KEY

IDS_PATH = os.getenv('IDS_PATH', '/api/v1/ids/data')
PROVIDER_IDS_BASE_URL = os.getenv('PROVIDER_IDS_BASE_URL', 'http://provider-control-plane:8282')
PROVIDER_IDS_ENDPOINT = f"{PROVIDER_IDS_BASE_URL}{IDS_PATH}"

# consumer side
CONSUMER_EDC_BASE_URL = os.getenv('CONSUMER_EDC_BASE_URL', 'http://consumer-control-plane:9193/api/v1/data')
assert CONSUMER_EDC_BASE_URL

CONSUMER_EDC_API_KEY = os.getenv('CONSUMER_EDC_API_KEY', 'dontuseinpublic')
assert CONSUMER_EDC_API_KEY

CONSUMER_EDC_VALIDATION_ENDPOINT = os.getenv('CONSUMER_EDC_VALIDATION_ENDPOINT', 'http://consumer-control-plane:9192/validation/token')

API_WRAPPER_BASE_URL = os.getenv('API_WRAPPER_BASE_URL', 'http://api-wrapper:9191/api/service')
assert API_WRAPPER_BASE_URL

API_WRAPPER_USER = os.getenv('API_WRAPPER_USER', 'someuser')
assert API_WRAPPER_USER

API_WRAPPER_PASSWORD = os.getenv('API_WRAPPER_PASSWORD', 'somepassword')
assert API_WRAPPER_PASSWORD

NR_OF_ASSETS = int(os.getenv('NR_OF_ASSETS', '1'))

DAPS_JWKS = os.getenv('DAPS_JWKS', 'http://daps-mock:8000/.well-known/jwks.json')
