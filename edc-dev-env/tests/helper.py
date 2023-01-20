import os
from uuid import uuid4
import requests
import pytest


PROVIDER_EDC_BASE_URL = os.getenv('PROVIDER_EDC_BASE_URL', 'http://provider-control-plane:9193/api/v1/data')
assert PROVIDER_EDC_BASE_URL

PROVIDER_EDC_API_KEY = os.getenv('PROVIDER_EDC_API_KEY', 'dontuseinpublic')
assert PROVIDER_EDC_API_KEY

# consumer side
API_WRAPPER_BASE_URL = os.getenv('API_WRAPPER_BASE_URL', 'http://api-wrapper:9191/api/service')
assert API_WRAPPER_BASE_URL

API_WRAPPER_USER = os.getenv('API_WRAPPER_USER', 'someuser')
assert API_WRAPPER_USER

API_WRAPPER_PASSWORD = os.getenv('API_WRAPPER_PASSWORD', 'somepassword')
assert API_WRAPPER_PASSWORD

NR_OF_ASSETS = int(os.getenv('NR_OF_ASSETS', '1'))


def prepare_data_management_auth():
    return {
        'X-Api-Key': PROVIDER_EDC_API_KEY
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


def create_asset(base_url: str = 'http://localhost'):
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
                #"proxyPath": True,
                "proxyMethod": True,
                "proxyBody": True,
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
