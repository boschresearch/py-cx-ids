# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from time import sleep
import json
import requests
from requests.auth import HTTPBasicAuth
import pytest
from uuid import uuid4

from tests.helper import create_asset, create_policy, create_contract_definition
from pycxids.edc.api import EdcConsumer
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_EDC_BASE_URL

# AAS / Registry
from pycxids.registry.api import Registry, CxRegistry
from pycxids.models.cxregistry import CxAas, CxSubmodelEndpoint
from pycxids.models.generated.registry import AssetAdministrationShellDescriptor, AssetAdministrationShellDescriptorCollection


API_WRAPPER_USER=os.getenv('API_WRAPPER_USER', 'someuser')
API_WRAPPER_PASSWORD=os.getenv('API_WRAPPER_PASSWORD', 'somepassword')
API_WRAPPER_BASE_URL = os.getenv('API_WRAPPER_BASE_URL', 'http://api-wrapper:9191')

REGISTRY_BASE_URL = os.getenv('REGISTRY_BASE_URL', 'http://registry:4243')


def test():
    """
    Test the 'old' and 'new' way of how assets are created and information is passed to the backend
    """
    # we create a new asset (and friends)
    asset_id = create_asset(base_url='http://dev:8001/returnparams/XXX', proxyPath=False)
    policy_id = create_policy(asset_id=asset_id)
    contract_id = create_contract_definition(policy_id=policy_id, asset_id=asset_id)

    # create registry entries
    registry = CxRegistry(base_url=REGISTRY_BASE_URL)
    aass:AssetAdministrationShellDescriptorCollection = registry.get_shell_descriptors()
    print(aass)

    aas = CxAas(
        submodels=[
            CxSubmodelEndpoint(
                endpoint_address="http://localhost",
                semantic_id="urn:cx:xxx"
            )
        ]
    )

    aas_created = registry.create(aas=aas)
    print(aas_created)

    aass:AssetAdministrationShellDescriptorCollection = registry.get_shell_descriptors()
    print(aass)


    sleep(1)
    
    # now, consumer side - for now with api-wrapper

    auth = HTTPBasicAuth(username=API_WRAPPER_USER, password=API_WRAPPER_PASSWORD)
    params = {
        "provider-connector-url": "http://provider-control-plane:8282",
    }
    url = f"{API_WRAPPER_BASE_URL}/{asset_id}/xxx"

    r = requests.get(url, auth=auth, params=params)

    if not r.ok:
        print(f"{r.reason} {r.content}")
        assert False, "Could not fetch data"
    
    print(r.content)



if __name__ == '__main__':
    pytest.main([__file__, "-s"])
