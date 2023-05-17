# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from hashlib import sha256
from urllib.parse import urlparse
import requests
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY
from pycxids.edc.api import EdcProvider
from pycxids.registry.api import Registry
from pycxids.models.generated.registry import AssetAdministrationShellDescriptorCollection, AssetAdministrationShellDescriptor

REGISTRY_ENDPOINT= os.getenv('REGISTRY_ENDPOINT', 'https://registry.dpp40-2-v2.industrialdigitaltwin.org/')


def create_edc_assets_from_registry_submodesl(registry_base_url: str, edc_data_managment_base_url: str, edc_auth_key: str):
    """
    Create assets for all endponts
    """
    endpoints = get_endpoints(registry_base_url=registry_base_url)
    asset_ids = create_edc_assets_from_list(
        endpoints=endpoints,
        edc_data_managment_base_url=edc_data_managment_base_url,
        edc_auth_key=edc_auth_key,
        proxyPath=False,
    )
    return asset_ids

def create_edc_assets_for_server_names(registry_base_url: str, edc_data_managment_base_url: str, edc_auth_key: str):
    """
    Create assets only for the servernames
    """
    endpoints = get_endpoints(registry_base_url=registry_base_url)
    server_names = get_servername_list_from_endpoints(endpoints=endpoints)
    asset_ids = create_edc_assets_from_list(
        endpoints=server_names,
        edc_data_managment_base_url=edc_data_managment_base_url,
        edc_auth_key=edc_auth_key,
        proxyPath=True,
    )
    return asset_ids


def get_endpoints(registry_base_url: str):
    """
    Get all AAS from the registry and filter for the relvant submodels and create a list of those endpoinAddress fields
    """
    endpoints = []
    registry: Registry = Registry(base_url=registry_base_url)
    aases:AssetAdministrationShellDescriptorCollection = registry.get_shell_descriptors()
    for aas in aases.items:
        for sm in aas.submodel_descriptors:
            for ep in sm.endpoints:
                ep_address = ep.protocol_information.endpoint_address
                endpoints.append(ep_address)
    return endpoints

def get_endpoint_hashes(registry_base_url: str):
    endpoints = get_endpoints(registry_base_url=registry_base_url)
    hashed_endpoints = []
    for endpoint in endpoints:
        h = hashed_asset_id(value=endpoint)
        hashed_endpoints.append(h)
    return hashed_endpoints

def get_servername_list_from_endpoints(endpoints:list):
    """
    From a list of endpoints, collect all server names and return a them.
    Each name only once.
    """
    server_names = []
    for endpoint in endpoints:
        server = get_servername(url=endpoint)
        server_names.append(server)
    return set(server_names)

def get_servername(url: str):
    server = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    return server

def hashed_asset_id(value: str):
    """
    Simple hash function to be used for the asset_id (from a given endpoint or server name)
    """
    asset_id = sha256(value.encode()).hexdigest()
    return asset_id

def create_edc_assets_from_list(endpoints:list, edc_data_managment_base_url: str, edc_auth_key: str, proxyPath = False):
    """
    Create a list of assets (and friends) for a given list.
    Prints out how many 'new' assets are created, but returns also the ones that could not be created,
    because those might already exist.
    """

    edc = EdcProvider(edc_data_managment_base_url=edc_data_managment_base_url, auth_key=edc_auth_key)

    counter = 0
    asset_ids = []
    for endpoint in endpoints:
        edc_asset_id = hashed_asset_id(value=endpoint)
        # we add all, not only newly created to the list
        asset_ids.append(edc_asset_id)
        edc_asset_id_created = edc.create_asset_and_friends(base_url=endpoint, asset_id=edc_asset_id, proxyQueryParams=True, proxyPath=proxyPath)[0]
        if edc_asset_id != edc_asset_id_created:
            print(f"Error: Something went wrong. Seems we could not create the asset. Continue with next submodel...")
            continue
        print(f"Created EDC asset for: {endpoint} asset_id: {edc_asset_id}")
        counter = counter + 1
    print(f"Created: {counter}")
    return asset_ids


if __name__ == '__main__':

    create_edc_assets_from_registry_submodesl(
        registry_base_url=REGISTRY_ENDPOINT,
        edc_data_managment_base_url=PROVIDER_EDC_BASE_URL,
        edc_auth_key=PROVIDER_EDC_API_KEY
    )

    server_name_asset_ids = create_edc_assets_for_server_names(
        registry_base_url=REGISTRY_ENDPOINT,
        edc_data_managment_base_url=PROVIDER_EDC_BASE_URL,
        edc_auth_key=PROVIDER_EDC_API_KEY
    )
    print(f"server name assets (some might not be newly created): {len(server_name_asset_ids)}")
