# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from time import sleep
import pytest
import requests
from requests.auth import HTTPBasicAuth
from pycxids.demo.i40pcf.init import create_edc_assets_from_registry_submodesl
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, API_WRAPPER_BASE_URL, API_WRAPPER_USER, API_WRAPPER_PASSWORD

from pycxids.registry.api import Registry
from pycxids.models.generated.registry import AssetAdministrationShellDescriptorCollection, AssetAdministrationShellDescriptor

registry: Registry = Registry(base_url='https://registry.dpp40-2-v2.industrialdigitaltwin.org/')

def test_fetch():

    aases:AssetAdministrationShellDescriptorCollection = registry.get_shell_descriptors()
    params = {
        "Email": "@phoenixcontact",
    }
    good = []
    bad = []
    for aas in aases.items:
        for sm in aas.submodel_descriptors:
            if sm.semantic_id and sm.semantic_id.value and len(sm.semantic_id.value) > 0 and 'https://zvei.org/demo/ProductCarbonFootprint/1/0' in sm.semantic_id.value:
                for ep in sm.endpoints:
                    ep_address = ep.protocol_information.endpoint_address
                    r = requests.get(ep_address, params=params)
                    if not r.ok:
                        bad.append(ep_address)
                        continue
                    good.append(ep_address)

    assert len(bad) == 0, "Could not fetch all endpoints"

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
