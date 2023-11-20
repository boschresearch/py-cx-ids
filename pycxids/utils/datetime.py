# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime

def datetime_now_utc():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
