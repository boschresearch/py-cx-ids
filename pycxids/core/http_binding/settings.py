import os
from pycxids.core.http_binding.models import OdrlOffer, OdrlPolicy, OdrlRule

# main storage
PROVIDER_STORAGE_FN = os.getenv('PROVIDER_STORAGE_FN', 'provider_storage.json')
# used mainly for backup and as a reference - not the main storage
PROVIDER_STORAGE_REQUESTS_FN = os.getenv('PROVIDER_STORAGE_REQUESTS_FN', 'provider_negotiation_requests.json')
# agreement storage
PROVIDER_STORAGE_AGREEMENTS_FN = os.getenv('PROVIDER_STORAGE_AGREEMENTS_FN', 'provider_agreements.json')
# separate transfer storage
PROVIDER_TRANSFER_STORAGE_FN = os.getenv('PROVIDER_TRANSFER_STORAGE_FN', 'provider_transfer_storage.json')

PROVIDER_CALLBACK_BASE_URL = os.getenv('PROVIDER_CALLBACK_BASE_URL', 'http://localhost:8080')
PROVIDER_DATA_DEFAULT_BASE_URL = os.getenv('PROVIDER_DATA_DEFAULT_BASE_URL', 'http://localhost:8080/data')

PROVIDER_DISABLE_IN_CONTEXT_WORKER = os.getenv('PROVIDER_DISABLE_IN_CONTEXT_WORKER', 'False').lower() in ['true']

# main storage
CONSUMER_STORAGE_FN = os.getenv('CONSUMER_STORAGE_FN', 'consumer_storage.json')
# used mainly for backup and as a reference - not the main storage
#CONSUMER_STORAGE_REQUESTS_FN = os.getenv('CONSUMER_STORAGE_REQUESTS_FN', 'consumer_negotiation_requests.json')
CONSUMER_STORAGE_AGREEMENTS_RECEIVED_FN = os.getenv('CONSUMER_STORAGE_AGREEMENTS_RECEIVED_FN', 'consumer_agreements_received.json')
CONSUMER_TRANSFER_STORAGE_FN = os.getenv('CONSUMER_TRANSFER_STORAGE_FN', 'consumer_transfer_storage.json')

CONSUMER_CALLBACK_BASE_URL = os.getenv('CONSUMER_CALLBACK_BASE_URL', 'http://localhost:6060')

CONSUMER_DISABLE_RECEIVER_API = os.getenv('CONSUMER_DISABLE_RECEIVER_API', 'False').lower() in ['true']

DATASPACE_PROTOCOL_HTTP = 'dataspace-protocol-http'
DCT_FORMAT_HTTP = 'dspace:HttpProxy' # TODO: what does EDC use here?

AUTH_CODE_REFERENCES_FN = os.getenv('AUTH_CODE_REFERENCES_FN', 'auth_code_references.json')


# http header fields
HTTP_HEADER_LOCATION = 'Location'
HTTP_HEADER_DEFAULT_AUTH_KEY = os.getenv('HTTP_HEADER_DEFAULT_AUTH_KEY', 'Authorization')

# storage keys
KEY_NEGOTIATION_REQUEST_ID = 'negotiation_request_id'
KEY_ID = 'id'
KEY_STATE = 'state'
KEY_DATASET = 'dataset'
KEY_AGREEMENT_ID  = 'agreement_id'
KEY_MODIFIED = 'modified'

KEY_TRANSFER_REQUEST_ID = 'transfer_request_id'
KEY_TRANSFER_ID = 'transfer_id'
KEY_TRANSFER_TOKEN = 'transfer_token'