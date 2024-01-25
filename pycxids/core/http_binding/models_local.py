# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
from pycxids.core.http_binding.settings import HTTP_HEADER_DEFAULT_AUTH_KEY
from pycxids.edc.api import EDC_NAMESPACE
from pycxids.models.base_model import MyBaseModel
from pycxids.core.http_binding.models import DcatCatalog, NegotiationState, TransferState

from pydantic import Field

# these are the not generated models, e.g. for storage


class NegotiationStateStore(MyBaseModel):
    id: str # provider_id
    tenant_id: Optional[str] = Field('')
    requester_bpn: Optional[str] = Field('')
    state: Optional[NegotiationState] = Field('')
    negotiation_request_id: Optional[str] = Field('')
    negotiation_callback_address: Optional[str] = Field()
    verification_message_id: Optional[str] = Field('')
    process_id: Optional[str] = Field('')
    dataset_id: Optional[str] = Field('')
    agreement_id: Optional[str] = Field('')

class DataAddress(MyBaseModel):
    """
    This is EDC specific. TODO: where to stanardize this?
    """
    field_type: Optional[str] = Field(f"{EDC_NAMESPACE}DataAddress", alias='@type') # TODO: EDC compat
    #edc_cid: Optional[str] = Field(None, alias='edc:cid') # no longer used in EDC 0.5.3
    edc_type: Optional[str] = Field("EDR", alias='edc:type')
    edc_auth_code: Optional[str] = Field(None, alias='edc:authCode')
    edc_endpoint: Optional[str] = Field(None, alias='edc:endpoint')
    edc_id: Optional[str] = Field(None, alias='edc:id')
    edc_auth_key: Optional[str] = Field(HTTP_HEADER_DEFAULT_AUTH_KEY, alias='edc:authKey')

class TransferStateStore(MyBaseModel):
    id: str # a provider id
    tenant_id: Optional[str] = Field('')
    state: Optional[TransferState]
    transfer_request_id: Optional[str] = Field('')
    callback_address_request: Optional[str]
    process_id: Optional[str]
    agreement_id: Optional[str]
    data_address: Optional[DataAddress]

class EdcCatalog(DcatCatalog):
    edc_participant_id: str = Field('', alias='edc:participantId')
