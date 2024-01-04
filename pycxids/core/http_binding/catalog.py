# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json

from pycxids.core.http_binding.models import CatalogRequestMessage, DcatCatalog, DcatDataset
from pycxids.core.http_binding.models_edc import AssetEntryNewDto

from pycxids.core.http_binding.policies import default_policy, default_offer_policy
from pycxids.core.http_binding.settings import KEY_MODIFIED, PROVIDER_STORAGE_ASSETS_FN
from pycxids.utils.storage import FileStorageEngine
from pycxids.core.jwt_decode import decode


def catalog_prepare_from_assets(assets) -> DcatCatalog:
    """
    TODO: Adds default policy to each asset / dataset
    """
    catalog = DcatCatalog()
    for item_id, item in assets:
        asset:AssetEntryNewDto = AssetEntryNewDto.parse_obj(item)
        dcat_dataset = DcatDataset(
            field_id = asset.asset.id,
            odrl_has_policy=[
                default_offer_policy
            ],
        )
        catalog.dcat_dataset.append(dcat_dataset)
    return catalog

def catalog_prepare_from_datasets(datasets) -> DcatCatalog:
    """
    datasets is a ready to go list of datasets including all offers / policies
    """
    catalog = DcatCatalog()
    catalog.dcat_dataset = datasets
    return catalog
