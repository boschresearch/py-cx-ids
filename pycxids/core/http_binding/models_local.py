# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
from pycxids.core.http_binding.settings import HTTP_HEADER_DEFAULT_AUTH_KEY
from pycxids.models.base_model import MyBaseModel
from pycxids.core.http_binding.models import NegotiationState, TransferState

from pydantic import Field

# these are the not generated models, e.g. for storage

class NegotiationStateStore(MyBaseModel):
    id: str
    state: NegotiationState
    negotiation_request_id: str
    dataset: str
    agreement_id: str

class DataAddress(MyBaseModel):
    """
    TODO: This is only temporary. We need to find out what EDC uses here exactly
    """
    field_type: Optional[str] = Field('DataAddress', alias='edc:type') # TODO: EDC compat
    auth_key: Optional[str] = Field(HTTP_HEADER_DEFAULT_AUTH_KEY, alias='edc:authKey')
    auth_code: Optional[str] = Field(None, alias='edc:authCode')
    base_url: Optional[str] = Field(None, alias='edc:baseUrl')

class TransferStateStore(MyBaseModel):
    id: str
    process_id: Optional[str] # @id from the request
    state: Optional[TransferState]
    agreement_id: Optional[str]
    callback_address_request: Optional[str]
    data_address: Optional[DataAddress]

default_context = {
    'dct': 'https://purl.org/dc/terms/',
    'tx': 'https://w3id.org/tractusx/v0.0.1/ns/',
    'edc': 'https://w3id.org/edc/v0.0.1/ns/',
    'dcat': 'https://www.w3.org/ns/dcat/',
    'odrl': 'http://www.w3.org/ns/odrl/2/',
    'dspace': 'https://w3id.org/dspace/v0.8/',
}

