#!/bin/bash
# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0


# pass in asset_id

curl http://someuser:somepassword@api-wrapper:9191/api/service/$1/xxx?provider-connector-url=http://provider-control-plane:8282 | jq
