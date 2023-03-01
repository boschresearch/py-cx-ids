# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Optional
import requests
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI, HTTPException, Query, Security, status, Request, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from pycxids.edc.api import EdcConsumer
from pycxids.edc.settings import CONSUMER_EDC_BASE_URL, CONSUMER_EDC_API_KEY, IDS_PATH, CONSUMER_EDC_VALIDATION_ENDPOINT
from pycxids.edc.settings import API_WRAPPER_USER, API_WRAPPER_PASSWORD
from pycxids.edc.settings import RECEIVER_SERVICE_BASE_URL
from pycxids.utils.storage import FileStorageEngine


app = FastAPI(title="api-wrapper compatible re-implementation")

# CORS configuration #
origins = [
    "*",
]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"])

API_WRAPPER_STORAGE_FN = os.getenv('API_WRAPPER_STORAGE_FN', 'api_wrapper_storage.json')

try:
    # 'cleaning' the cache database - dirty way of doing it
    os.remove(API_WRAPPER_STORAGE_FN)
except:
    pass
storage = FileStorageEngine(storage_fn=API_WRAPPER_STORAGE_FN)


def check_access(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    """
    Simple Basic Auth as with the original api-wrapper
    """
    try:
        if credentials.username == API_WRAPPER_USER and credentials.password == API_WRAPPER_PASSWORD:
            return True
    except Exception as ex:
        print(ex)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Something went wrong with authentication.")


@app.get('/api/service/{full_path:path}', dependencies=[Security(check_access)])
def get_endpoint(
        request: Request,
        full_path: str = Path('', description='{asset_id}/{sub_url}* - sub_url is optional'),
        provider_connector_url: str = Query(default="http://provider-control-plane:8282", alias="provider-connector-url"),
    ):
    """
    To receive all possible sub_urls (path behind the asset_id) and still make it optional,
    it seems we need to parse / split ourselve.
    What we acutally want is: '/api/service/{asset_id}/{sub_url}' where sub_url is optional
    """
    sub_url = ''
    parts = full_path.split('/')
    asset_id = parts[0]
    if len(parts) > 1:
        pos = full_path.find('/')
        sub_url = full_path[pos+1:]

    params = dict(request.query_params)
    del params['provider-connector-url'] # this one we handle separately and don't want to forward
    print(params)
    print(f"asset_id: {asset_id}")
    print(f"sub_url: {sub_url}")
    try:
        consumer = EdcConsumer(edc_data_managment_base_url=CONSUMER_EDC_BASE_URL, auth_key=CONSUMER_EDC_API_KEY)
        provider_ids_endpoint = provider_connector_url
        if not IDS_PATH in provider_ids_endpoint:
            # TODO: where to get reliable IDS_PATH from? or is this standardized?
            provider_ids_endpoint = provider_ids_endpoint + IDS_PATH
        # already have an agreement?
        agreement_id = storage.get(key=asset_id)
        if not agreement_id:
            # we need to negotiate
            catalog = consumer.get_catalog(provider_ids_endpoint=provider_ids_endpoint)
            offer = consumer.find_first_in_catalog(catalog=catalog, asset_id=asset_id)
            negotiation = consumer.negotiate_contract_and_wait(provider_ids_endpoint=provider_ids_endpoint, contract_offer=offer)
            agreement_id = negotiation.get('contractAgreementId')
            storage.put(key=asset_id, value=agreement_id)
        # for now let's fetch a new EDR token everytime. We could also check if we're still in the 10 minutes lifetime of it
        transfer_id = consumer.transfer(provider_ids_endpoint=provider_ids_endpoint, asset_id=asset_id, agreement_id=agreement_id)

        r = requests.get(f"{RECEIVER_SERVICE_BASE_URL}/{transfer_id}/token/consumer")
        if not r.ok:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not get EDR token in time.")

        j = r.json()
        consumer_endpoint = j.get('endpoint')
        auth_code = j.get('authCode')
        auth_key = j.get('authKey')

        url = f"{consumer_endpoint}{sub_url}"
        if sub_url and not sub_url.startswith('/') and not consumer_endpoint.endswith('/'):
            # fix / issues
            url = f"{consumer_endpoint}/{sub_url}"

        r = requests.get(url, headers={auth_key: f"{auth_code}"}, params=params)
        if not r.ok:
            print(f"{r.status_code} - {r.reason} - {r.content}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not fetch data.")
        j = r.json()
        return j

    except Exception as ex:
        print(ex)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ex))


def post_endpoint(path: str):
    pass


if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8080')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.apiwrapper.api_wrapper:app", host=host, port=int(port), workers=int(workers), reload=False)
