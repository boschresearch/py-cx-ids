import os
from pycxids.core.http_binding.models import OdrlOffer, OdrlPolicy, OdrlRule

# main storage
PROVIDER_STORAGE_FN = os.getenv('PROVIDER_STORAGE_FN', 'provider_storage.json')
# used mainly for backup and as a reference - not the main storage
PROVIDER_STORAGE_REQUESTS_FN = os.getenv('PROVIDER_STORAGE_REQUESTS_FN', 'provider_negotiation_requests.json')
# separate transfer storage
PROVIDER_TRANSFER_STORAGE_FN = os.getenv('PROVIDER_TRANSFER_STORAGE_FN', 'provider_transfer_storage.json')

PROVIDER_CALLBACK_BASE_URL = os.getenv('PROVIDER_CALLBACK_BASE_URL', 'http://localhost:8080')

PROVIDER_DISABLE_IN_CONTEXT_WORKER = os.getenv('PROVIDER_DISABLE_IN_CONTEXT_WORKER', 'False').lower() in ['true']

# main storage
CONSUMER_STORAGE_FN = os.getenv('CONSUMER_STORAGE_FN', 'consumer_storage.json')
# used mainly for backup and as a reference - not the main storage
#CONSUMER_STORAGE_REQUESTS_FN = os.getenv('CONSUMER_STORAGE_REQUESTS_FN', 'consumer_negotiation_requests.json')
CONSUMER_STORAGE_AGREEMENTS_RECEIVED_FN = os.getenv('CONSUMER_STORAGE_AGREEMENTS_RECEIVED_FN', 'consumer_agreements_received.json')

CONSUMER_CALLBACK_BASE_URL = os.getenv('CONSUMER_CALLBACK_BASE_URL', 'http://localhost:6060')

CONSUMER_DISABLE_RECEIVER_API = os.getenv('CONSUMER_DISABLE_RECEIVER_API', 'False').lower() in ['true']


KEY_NEGOTIATION_REQUEST_ID = 'negotiation_request_id'
KEY_ID = 'id'
KEY_STATE = 'state'
KEY_DATASET = 'dataset'
KEY_AGREEMENT_ID  = 'agreement_id'
KEY_MODIFIED = 'modified'
