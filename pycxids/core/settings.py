
# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseSettings, PrivateAttr, Field
import os

class Settings(BaseSettings):
    CLIENT_ID = ''
    CERT_FN = ''
    PRIVATE_KEY_FN = ''
    CONSUMER_CONNECTOR_URL = ""
    CONSUMER_CONNECTOR_URN = 'urn:uuid:consumer'
    CONSUMER_WEBHOOK = ""
    WEBHOOK_PORT = 6060
    DAPS_ENDPOINT = 'https://daps1.int.demo.catena-x.net/token'
    DAPS_JWKS_URL = 'https://daps1.int.demo.catena-x.net/.well-known/jwks.json'
    SCOPE = "idsc:IDS_CONNECTOR_ATTRIBUTES_ALL"
    ASSERTION_TYPE = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
    PROVIDER_CONNECTOR_URL = ""
    PROVIDER_CONNECTOR_IDS_ENDPOINT_PATH = "/api/v1/ids/data"

    class Config:
        env_file = os.getenv('ENV_FILE', '.env') # if ENV_FILE is not set, we read env vars from .env by default

settings: Settings = Settings()


CLIENT_ID = settings.CLIENT_ID
CERT_FN = settings.CERT_FN
CONSUMER_CONNECTOR_URL = settings.CONSUMER_CONNECTOR_URL
CONSUMER_CONNECTOR_URN = settings.CONSUMER_CONNECTOR_URN
CONSUMER_WEBHOOK = settings.CONSUMER_WEBHOOK


DAPS_ENDPOINT = settings.DAPS_ENDPOINT
SCOPE = settings.SCOPE
ASSERTION_TYPE = settings.ASSERTION_TYPE

PROVIDER_CONNECTOR_URL = settings.PROVIDER_CONNECTOR_URL
PROVIDER_CONNECTOR_IDS_ENDPOINT = settings.PROVIDER_CONNECTOR_URL + settings.PROVIDER_CONNECTOR_IDS_ENDPOINT_PATH

def endpoint_check(endpoint: str):
    if not '/api/v1/ids/data' in endpoint:
        endpoint = endpoint + '/api/v1/ids/data'
    return endpoint
