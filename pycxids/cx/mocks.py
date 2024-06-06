# Copyright (c) 2024 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from fastapi import FastAPI, Body
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI(title="CX mocked services")

app.add_middleware(GZipMiddleware, minimum_size=1)

@app.get('/bdrs/bpn-directory')
def bdrs_bpn_directory():
    """
    Mocked services for

    https://github.com/eclipse-tractusx/bpn-did-resolution-service


    /bdrs -> https://bpn-did-resolution-service.int.demo.catena-x.net/api/directory
    """
    bdrs = {
        "BPNL00000003CRHK": "did:web:dim-static-prod.dis-cloud-prod.cfapps.eu10-004.hana.ondemand.com:dim-hosted:2f45795c-d6cc-4038-96c9-63cedc0cd266:holder-iatp",
        "BPNL00000007ZS71": "did:web:portal-backend.int.demo.catena-x.net:api:administration:staticdata:did:BPNL00000007ZS71",
        "BPNL00000007ZS7X": "did:web:portal-backend.int.demo.catena-x.net:api:administration:staticdata:did:BPNL00000007ZS7X",
        "BPNLprovider": "did:web:todo",
        "BPNLconsumer": "did:web:todo",
    }
    return bdrs

@app.post('/portal/api/administration/connectors/discovery')
def portal_edc_discovery(body = Body(...)):
    """
    Mock the EDC Discovery service which is part of the Portal
    and returns the available EDC endpoints for a given BPN
    """
    bpn_endpoints = []
    for bpn in body:
        if bpn == 'BPNLprovider':
            bpn_endpoints.append(
                {
                    bpn: {
                        'connectorEndpoint': ['http://provider-control-plane:8282/api/v1/dsp']
                    }
                }
            )

        elif bpn == 'BPNLconsumer':
            bpn_endpoints.append(
                {
                    bpn: {
                        'connectorEndpoint': ['http://consumer-control-plane:8282/api/v1/dsp']
                    }
                }
            )

        else:
            bpn_endpoints.append(
                {
                    bpn: {
                        'connectorEndpoint': ['http://localhost']
                    }
                }
            )

    return bpn_endpoints

@app.post('/sts')
def sts_get_token(body: dict = Body(...)):
    """
    IATP:
    Creates the token that is sent with the DSP message which allows the receiver
    to fetch the actual VC/VPs from the Credential Service (CS)
    """
    pass

@app.post('/cs/presentations/query')
def credential_service_presentations_query(body: dict = Body()):
    """
    IATP:
    Request contains a token that describes which VC/VPs are returned.
    """
    pass

@app.post('/dummy/token')
def dummy_auth_token(body = Body(...)):
    """
    Returns a dummy JWT token that can be used with the other services for which
    e.g. EDC first fetches an auth token. Example STS
    """
    pass
