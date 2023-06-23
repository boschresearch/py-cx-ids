#!/usr/bin/env python3

# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from cli_settings import *
import requests

def fetch_catalog(catalog_endpoint: str, out_fn: str = ''):
    data = {}
    r = requests.post(catalog_endpoint, json=data)
    if not r.status_code == 200:
        print(f"status_code: {r.status_code} - reason: {r.reason} - details: {r.content}")
        return None
    j = r.json()
    return j

def get_asset_ids_from_catalog(catalog):
    datasets = catalog.get('dcat:dataset', [])
    asset_ids = []
    for d in datasets:
        dataset_id = d.get('@id')
        if dataset_id:
            asset_ids.append(dataset_id)
    return asset_ids