# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from time import sleep

import requests
from fastapi import status

from pycxids.core.http_binding.settings import KEY_DATASET, KEY_STATE, PROVIDER_CALLBACK_BASE_URL, PROVIDER_STORAGE_FN, PROVIDER_STORAGE_REQUESTS_FN, KEY_NEGOTIATION_REQUEST_ID, KEY_ID
from pycxids.core.http_binding.policies import default_policy
from pycxids.utils.storage import FileStorageEngine
from pycxids.core.http_binding.negotiation_states import Agreed, Requested, Offered
from pycxids.core.http_binding.models import ContractAgreementMessage, ContractRequestMessage, ContractOfferMessage, OdrlAgreement, OdrlOffer

storage = FileStorageEngine(storage_fn=PROVIDER_STORAGE_FN)
storage_negotiation_requests = FileStorageEngine(storage_fn=PROVIDER_STORAGE_REQUESTS_FN)

def worker_loop():
    while True:
        all = storage.get_all()
        for item in all:
            if item.get('state') == Requested.NAME:
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
    callback = negotation_request_message.dscpace_callback_address

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
        item[KEY_STATE] = Offered.NAME
        storage.put(id, item)

def requested_agreed(item):
    request_id = item.get(KEY_NEGOTIATION_REQUEST_ID)
    if not request_id:
        return
    data = storage_negotiation_requests.get(request_id)
    negotation_request_message = ContractRequestMessage.parse_obj(data)
    callback = negotation_request_message.dscpace_callback_address

    # send an agreement
    # TODO: of course in reality, we would need to check some details

    agreement = OdrlAgreement.parse_obj(default_policy)
    agreement.odrl_target = item.get(KEY_DATASET)
    id = item.get(KEY_ID)
    agreement_message = ContractAgreementMessage(
        field_id = id,
        dspace_process_id = request_id,
        dspace_agreement = agreement,
        dspace_callback_address = PROVIDER_CALLBACK_BASE_URL,
    )

    r = requests.post(url=f"{callback}/negotiations/{request_id}/agreement", data=agreement_message)
    if not r.ok:
        print(f"{r.status_code} - {r.reason} - {r.content}")
        return
    if r.status_code == status.HTTP_200_OK:
        # TODO: check read / write changes or lock
        item[KEY_STATE] = Agreed.NAME
        storage.put(id, item)


if __name__ == '__main__':
    worker_loop()