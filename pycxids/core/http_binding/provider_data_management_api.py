# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4
from fastapi import APIRouter, Body, Request, HTTPException, status, Query

from pycxids.core.http_binding.models_edc import AssetEntryNewDto, ContractDefinitionRequestDto, IdResponseDto, PolicyDefinitionRequestDto
from pycxids.core.http_binding.settings import KEY_MODIFIED, PROVIDER_STORAGE_ASSETS_FN
from pycxids.utils.storage import FileStorageEngine

app = APIRouter(tags=['EDC compatible data management API to e.g. create assets - customized, non-dsp API'])

storage_assets = FileStorageEngine(storage_fn=PROVIDER_STORAGE_ASSETS_FN, last_modified_field_name_isoformat=KEY_MODIFIED)

@app.post('/v2/assets', response_model=IdResponseDto)
def create_asset(asset: AssetEntryNewDto = Body(...)):
    """
    Creates a new asset together with a data address.

    Should be EDC compatible as much as possible
    """
    if not asset.asset.id:
        asset.asset.id = str(uuid4())
    storage_assets.put(asset.asset.id, asset.dict(exclude_unset=False))
    r = IdResponseDto(
        field_id = asset.asset.id, # TODO what to fill in here additionally?
    )
    return r

@app.post('/v2/policydefinitions')
def create_policy(policy: PolicyDefinitionRequestDto = Body(...)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail='Not implemented yet. Still using default policy only!')

@app.post('/v2/contractdefinitions')
def create_contract_definition(contract_definition: ContractDefinitionRequestDto = Body(...)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail='Not implemented yet. Still using default policy only!')
