# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import sys
import random
import pytest
from time import sleep
from pycxids.edc.api import EdcConsumer, EdcProvider
from pycxids.edc.settings import CONSUMER_EDC_API_KEY, CONSUMER_EDC_BASE_URL, PROVIDER_IDS_ENDPOINT
from pycxids.edc.settings import PROVIDER_EDC_API_KEY, PROVIDER_EDC_BASE_URL, DAPS_JWKS, NR_OF_ASSETS, NR_OF_CALLS



def test_catalog():
    provider = EdcProvider(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)

    for i in range(0,NR_OF_ASSETS):
        provider.create_asset_and_friends(base_url=DAPS_JWKS)

    consumer = EdcConsumer(edc_data_managment_base_url=CONSUMER_EDC_BASE_URL, auth_key=CONSUMER_EDC_API_KEY)
    counter = 0
    while True:
        try:
            page = random.randint(1, 5)
            catalog = consumer.get_catalog(provider_ids_endpoint=PROVIDER_IDS_ENDPOINT)
            counter = counter + 1
            if counter >= NR_OF_CALLS:
                print(f"reached: {counter}")
                break
            nr = len(catalog['contractOffers'])
            print(f"{nr}.", end='')
            #sleep(0.001)
        except Exception as ex:
            print(ex)
            print(counter)
            assert False, f"Exception in catalog call counter: {counter} of {NR_OF_CALLS}"
    
    assert True

if __name__ == '__main__':
    pytest.main([__file__, "-s"])