# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from base64 import b64encode
import os
from fastapi import FastAPI, Body, Request, HTTPException, status
import requests

from pycxids.core.http_binding.catalog_fastapi import app as catalog
from pycxids.core.http_binding.models_edc import Asset, AssetEntryNewDto, DataAddress as EdcDataAddress
from pycxids.core.http_binding.negotiation_provider_api import app as negotiation_provider
from pycxids.core.http_binding.transfer_provider_api import app as transfer_provider
from pycxids.core.http_binding.demo_data_backend import app as data_backend
from pycxids.core.http_binding.provider_data_management_api import create_asset, app as data_management

from pycxids.core.http_binding.settings import ASSET_PROP_BACKEND_PUBLIC_KEY, PROVIDER_CALLBACK_BASE_URL, settings
from pycxids.core.http_binding.crypto_utils import generate_rsa_keys_to_file

app = FastAPI(title="IDS http binding", version='0.8')

app.include_router(catalog)
app.include_router(negotiation_provider)
app.include_router(transfer_provider)
app.include_router(data_management)

# for demo purposes
app.include_router(data_backend)

@app.on_event("startup")
def on_startup():
    print("startup")
    print(f"Using PROVIDER_PARTICIPANT_ID: {settings.PROVIDER_PARTICIPANT_ID}")
    if not os.path.exists(settings.PROVIDER_PRIVATE_KEY_PKCS8_FN):
        generate_rsa_keys_to_file(public_key_fn=settings.PROVIDER_PUBLIC_KEY_PEM_FN, private_key_fn=settings.PROVIDER_PRIVATE_KEY_PKCS8_FN)
    if not os.path.exists(settings.BACKEND_PRIVATE_KEY_PKCS8_FN):
        generate_rsa_keys_to_file(public_key_fn=settings.BACKEND_PUBLIC_KEY_PEM_FN, private_key_fn=settings.BACKEND_PRIVATE_KEY_PKCS8_FN)
    backend_public_key = ''
    with open(settings.BACKEND_PUBLIC_KEY_PEM_FN, 'rb') as f:
        backend_public_key = f.read()
    
    # always create 1 dummy asset on startup with the valid pub key information
    # Provider: create an asset
    asset_id = 'demo_asset'
    asset:AssetEntryNewDto = AssetEntryNewDto(
        asset=Asset(
            id=asset_id,
            properties={
                ASSET_PROP_BACKEND_PUBLIC_KEY: b64encode(backend_public_key).decode(),
            }
        ),
        dataAddress=EdcDataAddress(
            properties={
                'type': 'HttpData',
                'baseUrl': f"{PROVIDER_CALLBACK_BASE_URL}/data/{asset_id}"
            }
        )
    )
    create_asset(asset=asset)
    