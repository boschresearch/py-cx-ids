# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from fastapi import APIRouter, Body, Header, Request, HTTPException, status
from pycxids.core.http_binding.catalog import catalog_prepare_from_assets, catalog_prepare_from_datasets

from pycxids.core.http_binding.models import CatalogRequestMessage, DcatCatalog, DcatDataset
from pycxids.core.http_binding.models_edc import AssetEntryNewDto

from pycxids.core.http_binding.policies import default_policy, default_offer_policy
from pycxids.core.http_binding.settings import KEY_MODIFIED, PROVIDER_STORAGE_ASSETS_FN, settings
from pycxids.utils.storage import FileStorageEngine
from pycxids.core.jwt_decode import decode

storage_assets = FileStorageEngine(storage_fn=PROVIDER_STORAGE_ASSETS_FN, last_modified_field_name_isoformat=KEY_MODIFIED)


app = APIRouter(tags=['Catalog'])

@app.post('/catalog/request')
def catalog_post(request: Request, body:dict = Body(...), authorization: str = Header(...)):
    auth_token = decode(authorization)
    del auth_token['signature']
    print(json.dumps(auth_token, indent=4))
    catalog_request_message: CatalogRequestMessage = CatalogRequestMessage.parse_obj(body)
    
    data = storage_assets.get_all().items()

    participant_id = settings.PROVIDER_PARTICIPANT_ID
    catalog = catalog_prepare_from_assets(assets=data, participant_id=participant_id)
    
    return catalog

@app.get('/catalog/datasets/{id}', response_model=DcatDataset)
def catalog_get(id: str):
    data = storage_assets.get(id)
    if data:
        asset:AssetEntryNewDto = AssetEntryNewDto.parse_obj(data)
        dcat_dataset = DcatDataset(
            field_id = asset.asset.id,
                odrl_has_policy=[
                    default_offer_policy
                ],
        )
        catalog = catalog_prepare_from_datasets([dcat_dataset])
        return catalog

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find asset with id: {id}")
