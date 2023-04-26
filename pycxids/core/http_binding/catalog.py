# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from fastapi import APIRouter, Body, Request, HTTPException, status

from pycxids.core.http_binding.models import CatalogRequestMessage, DcatCatalog, DcatDataset

from pycxids.core.http_binding.policies import default_policy

# some dummy assets for now
assets = [
    DcatDataset(
        field_id = 'dummy1',
        odrl_has_policy=[
            default_policy
        ],
    )
]


app = APIRouter(tags=['Catalog'])

@app.post('/catalog/request', response_model=DcatCatalog)
def catalog_post(catalog_request_message: CatalogRequestMessage = Body(...)):
    catalog = DcatCatalog(
        dcat_dataset=assets
    )
    return catalog

@app.get('/catalog/datasets/{id}', response_model=DcatDataset)
def catalog_get(id: str):
    for asset in assets:
        if asset.field_id == id:
            return asset

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find asset with id: {id}")
