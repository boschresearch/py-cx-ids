#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os

from pycxids.utils.storage import FileStorageEngine


PROTOCOL_DSP = 'DSP'
PROTOCOL_MULTIPART = 'multipart'

AGREEMENT_CACHE_DIR = os.getenv('AGREEMENT_CACHE_DIR', 'agreementcache')
os.makedirs(AGREEMENT_CACHE_DIR, exist_ok=True)

SETTINGS_STORAGE = os.getenv('SETTINGS_STORAGE', 'cli_settings.json')
config_storage = FileStorageEngine(storage_fn=SETTINGS_STORAGE)
