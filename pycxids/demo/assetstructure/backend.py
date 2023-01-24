import os
from json import JSONDecodeError
from uuid import uuid4
from typing import Optional
import requests
from fastapi import FastAPI, Request, Header, Body, HTTPException, Query
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pycxids.edc.api import EdcDataManagement
from pycxids.edc.settings import PROVIDER_EDC_BASE_URL, PROVIDER_EDC_API_KEY

app = FastAPI(title="Data Source / Backend System")


@app.get('/data')
def get_data(request: Request, authorization = Header(default=None)):
    print(request)
    token = request.query_params.get('token', None)
    if not token:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="No token provided in the token query param.")

    r = requests.get('http://provider-control-plane:9192/validation/token', headers={'Authorization': token})
    if not r.ok:
        print(f"{r.reason} - {r.content}")
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Could not validate token.")

    j = r.json()
    print(j)
    


    return {'hello': 'world'}

@app.get('/datawithagreementid')
def get_data_with_agreement_id(agreement_id: str = Query('', alias='agreementId')):
    edc = EdcDataManagement(edc_data_managment_base_url=PROVIDER_EDC_BASE_URL, auth_key=PROVIDER_EDC_API_KEY)
    agreement = edc.get(f"/contractagreements/{agreement_id}")
    if not agreement:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=f"Could not find an greement for the given agreementId: {agreement_id}")
    print(agreement)

    return agreement    # return this for demo purposes only!

if __name__ == '__main__':
    import uvicorn
    port = os.getenv('PORT', '8000')
    host = os.getenv('HOST', "0.0.0.0")
    workers = os.getenv('WORKERS', '1')
    uvicorn.run("pycxids.demo.assetstructure.backend:app", host=host, port=int(port), workers=int(workers), reload=False)
