# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os

PORTAL_OAUTH_TOKEN_ENDPOINT = os.getenv('PORTAL_OAUTH_TOKEN_ENDPOINT', 'https://centralidp.int.demo.catena-x.net/auth/realms/CX-Central/protocol/openid-connect/token')
PORTAL_BASE_URL = os.getenv('PORTAL_BASE_URL', 'https://portal-backend.int.demo.catena-x.net')

PORTAL_CLIENT_ID = os.getenv('PORTAL_CLIENT_ID', '')
#assert PORTAL_CLIENT_ID
PORTAL_CLIENT_SECRET = os.getenv('PORTAL_CLIENT_SECRET', '')
#assert PORTAL_CLIENT_SECRET
