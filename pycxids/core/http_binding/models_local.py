# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
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
    auth_key: Optional[str] = Field('Authorization', alias='authKey')
    auth_code: Optional[str] = Field(None, alias='authCode')
    base_url: Optional[str] = Field(None, alias='baseUrl')

class TransferStateStore(MyBaseModel):
    id: str
    process_id: str # @id from the request
    state: TransferState
    agreement_id: str
    callback_address_request: str
    data_address: DataAddress

