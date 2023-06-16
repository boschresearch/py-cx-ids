# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from fastapi import APIRouter, Body, Request, HTTPException, status

from pycxids.core.http_binding.models import CatalogRequestMessage, DcatCatalog, DcatDataset
from pycxids.core.http_binding.models_edc import AssetEntryNewDto

from pycxids.core.http_binding.policies import default_policy
from pycxids.core.http_binding.settings import KEY_MODIFIED, PROVIDER_STORAGE_ASSETS_FN
from pycxids.utils.storage import FileStorageEngine

storage_assets = FileStorageEngine(storage_fn=PROVIDER_STORAGE_ASSETS_FN, last_modified_field_name_isoformat=KEY_MODIFIED)


app = APIRouter(tags=['Catalog'])

@app.post('/catalog/request', response_model=DcatCatalog)
def catalog_post(catalog_request_message: CatalogRequestMessage = Body(...)):
    catalog = DcatCatalog(
        dcat_dataset=[],
    )

    data = storage_assets.get_all().items()
    for item_id, item in data:
        asset:AssetEntryNewDto = AssetEntryNewDto.parse_obj(item)
        dcat_dataset = DcatDataset(
            field_id = asset.asset.id,
            odrl_has_policy=[
                default_policy
            ],
        )
        catalog.dcat_dataset.append(dcat_dataset)
    return catalog

@app.get('/catalog/datasets/{id}', response_model=DcatDataset)
def catalog_get(id: str):
    data = storage_assets.get(id)
    if data:
        asset:AssetEntryNewDto = AssetEntryNewDto.parse_obj(data)
        dcat_dataset = DcatDataset(
            field_id = asset.asset.id,
                odrl_has_policy=[
                    default_policy
                ],
        )
        return dcat_dataset

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find asset with id: {id}")
