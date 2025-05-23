# Copyright (c) 2025 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os


STS_BASE_URL = os.getenv('IATP_BASE_URL', 'http://cx-services-mocks:8080')

STS_CLIENT_ID = os.getenv('STS_CLIENT_ID', 'client')
STS_CLIENT_SECRET = os.getenv('STS_CLIENT_SECRET', 'secret')
STS_TOKEN_URL = os.getenv('STS_TOKEN_URL', 'http://cx-services-mocks:8080/dummy/token')
STS_OUR_DID = os.getenv('STS_OUR_DID', 'did:web:http://cx-services-mocks:8080/')
