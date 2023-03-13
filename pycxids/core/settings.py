
# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseSettings, PrivateAttr, Field
import os

class Settings(BaseSettings):
    CLIENT_ID = 'consumer'
    CERT_FN = ''
    PRIVATE_KEY_FN = './edc-dev-env/vault_secrets/consumer.key'
    CONSUMER_CONNECTOR_URL = ""
    CONSUMER_CONNECTOR_URN = 'urn:uuid:consumer'
    CONSUMER_WEBHOOK = "http://dev:6060/webhook"
    WEBHOOK_PORT = 6060
    DAPS_ENDPOINT = 'http://daps-mock:8000/token'
    DAPS_JWKS_URL = 'http://daps-mock:8000/.well-known/jwks.json'
    SCOPE = "idsc:IDS_CONNECTOR_ATTRIBUTES_ALL"
    ASSERTION_TYPE = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
    PROVIDER_CONNECTOR_URL = ""
    PROVIDER_CONNECTOR_IDS_ENDPOINT_PATH = "/api/v1/ids/data"
    # webhook service usage
    CONSUMER_WEBHOOK_MESSAGE_BASE_URL = ""
    CONSUMER_WEBHOOK_MESSAGE_USERNAME = "someuser"
    CONSUMER_WEBHOOK_MESSAGE_PASSWORD = "somepassword"

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

BASIC_AUTH_USERNAME = os.getenv('BASIC_AUTH_USERNAME', 'someuser')
BASIC_AUTH_PASSWORD = os.getenv('BASIC_AUTH_PASSWORD', 'somepassword')

def endpoint_check(endpoint: str):
    if not '/api/v1/ids/data' in endpoint:
        endpoint = endpoint + '/api/v1/ids/data'
    return endpoint
