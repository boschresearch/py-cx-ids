# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from fastapi import APIRouter, Body, Request, HTTPException, status

from pycxids.core.http_binding.models import ContractRequestMessage, ContractNegotiation

app = APIRouter(tags=['Negotiaion'])

@app.post('/negotiations/request', response_model=ContractNegotiation)
def negotiation_request(contract_request: ContractRequestMessage = Body(...)):
    pass

@app.get('/negotiations/{id}', response_model=ContractNegotiation)
def negotiation_get(id: str):
    pass

