# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from time import sleep
from datetime import datetime
from uuid import uuid4
import requests
from fastapi import status

from pycxids.core.daps import Daps
from pycxids.core.settings import settings as core_settings
from pycxids.core.http_binding.settings import KEY_AGREEMENT_ID, KEY_DATASET, KEY_PROCESS_ID, KEY_STATE, PROVIDER_CALLBACK_BASE_URL, PROVIDER_STORAGE_AGREEMENTS_FN, PROVIDER_STORAGE_FN, PROVIDER_STORAGE_REQUESTS_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID, KEY_MODIFIED
from pycxids.core.http_binding.policies import default_policy
from pycxids.utils.storage import FileStorageEngine
from pycxids.core.http_binding.models import ContractAgreementMessage, ContractNegotiationEventMessage, ContractRequestMessage, ContractOfferMessage, DspaceEventType, DspaceTimestamp, OdrlAgreement, OdrlOffer, NegotiationState

storage = FileStorageEngine(storage_fn=PROVIDER_STORAGE_FN, last_modified_field_name_isoformat=KEY_MODIFIED)
storage_negotiation_requests = FileStorageEngine(storage_fn=PROVIDER_STORAGE_REQUESTS_FN, last_modified_field_name_isoformat=KEY_MODIFIED)
# references storage doesn't make sense to have modified, because the value is no object!
storage_agreements = FileStorageEngine(storage_fn=PROVIDER_STORAGE_AGREEMENTS_FN)

def worker_loop():
    while True:
        all = storage.get_all()
        for item in all:
            if item.get('state') == NegotiationState.requested:
                # Transition: Requested -> Offered
                #requested_offered(item=item)

                # for now we always to the most simple case:
                # Transition: Requested -> Agreed
                requested_agreed(item=item)

        sleep(2)

def requested_offered(item):
    """
    Transition Requested -> Offered
    """
    request_id = item.get(KEY_NEGOTIATION_REQUEST_ID)
    if not request_id:
        return
    data = storage_negotiation_requests.get(request_id)
    negotation_request_message = ContractRequestMessage.parse_obj(data)
    callback = negotation_request_message.dspace_callback_address

    # send an offer
    # TODO: of course in reality, we would need to check some details
    offer = OdrlOffer.parse_obj(default_policy)
    offer.odrl_target = item.get(KEY_DATASET)
    id = item.get(KEY_ID)
    offer_message = ContractOfferMessage(
        field_id = id,
        dspace_process_id = request_id,
        dspace_offer = offer,
        dspace_callback_address = PROVIDER_CALLBACK_BASE_URL,
    )

    r = requests.post(url=f"{callback}/negotiations/{request_id}/offers", data=offer_message)
    if not r.ok:
        print(f"{r.status_code} - {r.reason} - {r.content}")
        return
    if r.status_code == status.HTTP_200_OK:
        # TODO: check read / write changes or lock
        item[KEY_STATE] = NegotiationState.offered
        storage.put(id, item)

async def requested_agreed(item, offer: dict = None):
    """
    Requested -> Agreeed

    item: custom storage item
    """
    request_id = item.get(KEY_NEGOTIATION_REQUEST_ID)
    process_id = item.get(KEY_PROCESS_ID)
    dataset_id = item.get(KEY_DATASET)
    item_id = item.get(KEY_ID)
    if not request_id:
        return
    data = storage_negotiation_requests.get(request_id)
    negotation_request_message = ContractRequestMessage.parse_obj(data)
    callback = negotation_request_message.dspace_callback_address

    # send an agreement
    # TODO: of course in reality, we would need to check some details

    now = datetime.utcnow()

    agreement_id = f"{str(uuid4())}:{str(uuid4())}:{str(uuid4())}"  # the agreement id must be newly created, don't reuse an existing id to avoid id mis-use

    # agreement = OdrlAgreement.parse_obj(offer.dict())
    # agreement.odrl_target = dataset_id
    # agreement.dspace_provider_id = 'BPNLprovider' # TODO:
    # agreement.dspace_consumer_id = 'consumer' # TODO: get from message
    # agreement.dspace_timestamp = DspaceTimestamp(field_value=now.strftime('%Y-%m-%dT%H:%M:%SZ')) # TODO: py does not support military Z, put in utils
    agreement = offer
    agreement['odrl:target'] = dataset_id
    agreement['dspace:providerId'] = 'BPNLprovider'
    agreement['dspace:consumerId'] = 'consumer'
    agreement['dspace:timestamp'] = DspaceTimestamp(field_value=now.strftime('%Y-%m-%dT%H:%M:%SZ')).dict() # TODO: py does not support military Z, put in utils

    # at least EDC uses the agreement id from here, not from the enclosing message
    agreement['@id']= agreement_id
    
    # store reference agreement_id -> negotiation id
    storage_agreements.put(agreement_id, item_id)
    agreement_message = ContractAgreementMessage(
        field_id = str(uuid4()), # not relevant, since not used in EDC anywhere
        dspace_process_id = process_id,
        #dspace_agreement = agreement,
        dspace_callback_address = PROVIDER_CALLBACK_BASE_URL,
    )
    data = agreement_message.dict()
    data['dspace:agreement'] = agreement
    # data['dspace:agreement']['permission'][0]['action'] = {
    #     "odrl:type": "USE"
    # }
    # we need a daps token first
    daps = Daps(daps_endpoint=core_settings.DAPS_ENDPOINT, private_key_fn=core_settings.PRIVATE_KEY_FN, client_id=core_settings.CLIENT_ID)
    token = daps.get_daps_token(audience=callback)
    headers = {
        'Authorization': token['access_token']
    }
    # TODO: check if the process_id here is correct behavior from EDC and this is DSP spec compliant
    try:
        r = requests.post(url=f"{callback}/negotiations/{process_id}/agreement", json=data, headers=headers)
        if not r.status_code == status.HTTP_200_OK:
            print(f"{r.status_code} - {r.reason} - {r.content}")
            return
        if r.status_code == status.HTTP_200_OK:
            # TODO: check read / write changes or lock
            item[KEY_STATE] = NegotiationState.agreed
            item[KEY_AGREEMENT_ID] = agreement_id
            storage.put(item_id, item)
    except Exception as ex:
        print(ex)

async def verified_finalized(id: str, msg: dict):
    """
    VERIFIED -> FINALIZED

    Provider only
    """
    process_id = msg.get('dspace:processId')
    negotiation_event_msg = ContractNegotiationEventMessage(
        dspace_process_id = process_id,
        dspace_event_type = DspaceEventType(DspaceEventType.https___w3id_org_dspace_v0_8_finalized)
    )
    callback = None
    # TODO: do this in a better way, maybe a mapping from processId to our provider set id
    all_negotations = storage_negotiation_requests.get_all()
    for key, value in all_negotations.items():
        value_pid = value.get('dspace:processId')
        if value_pid == id:
            callback = value.get('dspace:callbackAddress')
            break
    if not callback:
        print(f"Could not find callback address for processId: {id}")
        return
    data = negotiation_event_msg.dict()
    try:
        daps = Daps(daps_endpoint=core_settings.DAPS_ENDPOINT, private_key_fn=core_settings.PRIVATE_KEY_FN, client_id=core_settings.CLIENT_ID)
        token = daps.get_daps_token(audience=callback)
        headers = {
            'Authorization': token['access_token']
        }

        r = requests.post(url=f"{callback}/negotiations/{process_id}/events", json=data, headers=headers)
        if not r.status_code == status.HTTP_200_OK:
            print(f"{r.status_code} - {r.reason} - {r.content}")
            return
        if r.status_code == status.HTTP_200_OK:
            # TODO: check read / write changes or lock
            # TODO: put to storage
            pass
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    worker_loop()
