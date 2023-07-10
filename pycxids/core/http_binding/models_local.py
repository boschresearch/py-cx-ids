# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
from pycxids.core.http_binding.settings import HTTP_HEADER_DEFAULT_AUTH_KEY
from pycxids.edc.api import EDC_NAMESPACE
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
    This is EDC specific. TODO: where to stanardize this?
    """
    field_type: Optional[str] = Field(f"{EDC_NAMESPACE}DataAddress", alias='@type') # TODO: EDC compat
    edc_cid: Optional[str] = Field(None, alias='edc:cid')
    edc_type: Optional[str] = Field("EDR", alias='edc:type')
    edc_auth_code: Optional[str] = Field(None, alias='edc:authCode')
    edc_endpoint: Optional[str] = Field(None, alias='edc:endpoint')
    edc_id: Optional[str] = Field(None, alias='edc:id')
    edc_auth_key: Optional[str] = Field(HTTP_HEADER_DEFAULT_AUTH_KEY, alias='edc:authKey')

class TransferStateStore(MyBaseModel):
    id: str
    process_id: Optional[str] # @id from the request
    state: Optional[TransferState]
    agreement_id: Optional[str]
    callback_address_request: Optional[str]
    data_address: Optional[DataAddress]

