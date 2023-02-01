# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from uuid import uuid4
import requests
import pytest
from pycxids.edc.settings import NR_OF_ASSETS, PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY, CONSUMER_EDC_API_KEY


def prepare_data_management_auth():
    return {
        'X-Api-Key': PROVIDER_EDC_API_KEY
    }

def prepare_consumer_data_management_auth():
    return {
        'X-Api-Key': CONSUMER_EDC_API_KEY
    }


def get_number_of_elements(endpoint):
    """
    """
    try:
        r = requests.get(endpoint, headers=prepare_data_management_auth(), params={ 'limit': NR_OF_ASSETS * 2 })
        j = r.json()
        return len(j)
    except Exception as ex:
        print(ex)
        return None


def create_asset(base_url: str = 'http://localhost', proxyPath=False, proxyQueryParams=False, proxyBody=False, proxyMethod=False):
    asset_id = str(uuid4())
    data = {
        "asset": {
            "properties": {
                "asset:prop:id": asset_id,
                "asset:prop:contenttype": "application/json",
                "asset:prop:policy-id": "use-eu",
            }
        },
        "dataAddress": {
            "properties": {
                "type": "HttpData",
                "proxyPath": proxyPath,
                "proxyQueryParams": proxyQueryParams,
                "proxyMethod": proxyMethod,
                "proxyBody": proxyBody,
                "baseUrl": base_url,
            }
        }
    }

    r = requests.post(f"{PROVIDER_EDC_BASE_URL}/assets", json=data, headers=prepare_data_management_auth())
    if not r.ok:
        return None
    # TODO: checks
    return asset_id

def create_contract_definition(policy_id: str, asset_id: str):
    cd_id = str(uuid4())
    data = {
        "id": cd_id,
        "accessPolicyId": policy_id,
        "contractPolicyId": policy_id,
        "criteria": [
            {
                "operandLeft": "asset:prop:id",
                "operator": "=",
                "operandRight": asset_id
            }
        ],
    }
    r = requests.post(f"{PROVIDER_EDC_BASE_URL}/contractdefinitions", json=data, headers=prepare_data_management_auth())
    return cd_id


def get_contract_definition(id: str):
    r = requests.get(f"{PROVIDER_EDC_BASE_URL}/contractdefinitions/{id}", headers=prepare_data_management_auth())
    if r.ok:
        j = r.json()
        return j
    return None

def create_policy(asset_id: str):
    policy_id = str(uuid4())
    data = {
        "id": policy_id,
        "policy": {
            "permissions": [
                {
                    "target": asset_id,
                    "action": {
                        "type": "USE"
                    },
                    "edctype": "dataspaceconnector:permission"
                }
            ],
        },
        "@type": {
            "@policytype": "set"
        }
    }
    r = requests.post(f"{PROVIDER_EDC_BASE_URL}/policydefinitions", json=data, headers=prepare_data_management_auth())
    return policy_id

@pytest.fixture
def edc_is_clean():
    """
    True if assets, policiesand contractdefinitions are empty (or not fetchable)
    """
    nr_of_assets = get_number_of_elements(f"{PROVIDER_EDC_BASE_URL}/assets")
    nr_of_policies = get_number_of_elements(f"{PROVIDER_EDC_BASE_URL}/policydefinitions")
    nr_of_contractdefinitions = get_number_of_elements(f"{PROVIDER_EDC_BASE_URL}/contractdefinitions")

    return nr_of_assets == nr_of_policies == nr_of_contractdefinitions == 0
