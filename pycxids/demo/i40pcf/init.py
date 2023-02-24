# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from hashlib import sha256
import requests
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY
from pycxids.edc.api import EdcProvider
from pycxids.registry.api import Registry
from pycxids.models.generated.registry import AssetAdministrationShellDescriptorCollection, AssetAdministrationShellDescriptor

def create_edc_assets_from_registry_submodesl(registry_base_url: str, edc_data_managment_base_url: str, edc_auth_key: str):
    
    registry: Registry = Registry(base_url=registry_base_url)

    edc = EdcProvider(edc_data_managment_base_url=edc_data_managment_base_url, auth_key=edc_auth_key)

    counter = 0
    asset_ids = []
    aases:AssetAdministrationShellDescriptorCollection = registry.get_shell_descriptors()
    for aas in aases.items:
        for sm in aas.submodel_descriptors:
            if sm.semantic_id and sm.semantic_id.value and len(sm.semantic_id.value) > 0 and 'https://zvei.org/demo/ProductCarbonFootprint/1/0' in sm.semantic_id.value:
                for ep in sm.endpoints:
                    ep_address = ep.protocol_information.endpoint_address
                    edc_asset_id = sha256(ep_address.encode()).hexdigest()
                    # we add all, not only newly created to the list
                    asset_ids.append(edc_asset_id)
                    edc_asset_id_created = edc.create_asset(base_url=ep_address, asset_id=edc_asset_id, proxyQueryParams=True, try_delete_before_create=True)
                    if edc_asset_id != edc_asset_id_created:
                        print(f"Error: Something went wrong. Seems we could not create the asset. Continue with next submodel...")
                        continue
                    policy_id = edc.create_policy(asset_id=edc_asset_id)
                    cd_id = edc.create_contract_definition(policy_id=policy_id, asset_id=edc_asset_id)
                    print(f"Created EDC asset for: {ep_address} asset_id: {edc_asset_id}")
                    counter = counter + 1
    print(f"Created: {counter}")
    return asset_ids


if __name__ == '__main__':
    create_edc_assets_from_registry_submodesl(
        registry_base_url='https://registry.dpp40-2-v2.industrialdigitaltwin.org/',
        edc_data_managment_base_url=PROVIDER_EDC_BASE_URL,
        edc_auth_key=PROVIDER_EDC_API_KEY
    )
