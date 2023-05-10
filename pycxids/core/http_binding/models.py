# generated by datamodel-codegen:
#   filename:  http_binding_openapi.yaml
#   timestamp: 2023-04-27T08:51:20+00:00

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pycxids.models.base_model import MyBaseModel
from pydantic import Field


class DspaceFilter(MyBaseModel):
    pass


class CatalogRequestMessage(MyBaseModel):
    field_context: Optional[str] = Field(
        'https://w3id.org/dspace/v0.8/context.json', alias='@context'
    )
    field_type: Optional[str] = Field('dspace:CatalogRequestMessage', alias='@type')
    filter: Optional[DspaceFilter] = None


class DspaceEventType(Enum):
    finalized = 'FINALIZED'
    accepted = 'ACCEPTED'
    terminated = 'TERMINATED'


class ContracNegotiationEventMessage(MyBaseModel):
    field_context: Optional[str] = Field(
        'https://w3id.org/dspace/v0.8/context.json', alias='@context'
    )
    field_type: Optional[str] = Field(
        'dspace:ContractNegotiationEventMessage', alias='@type'
    )
    dspace_process_id: Optional[str] = Field(None, alias='dspace:processId')
    dspace_event_type: Optional[DspaceEventType] = Field(None, alias='dspace:eventType')
    dspace_checksum: Optional[str] = Field(None, alias='dspace:checksum')


class DspaceState(Enum):
    requested = 'REQUESTED'
    offered = 'OFFERED'
    accepted = 'ACCEPTED'
    agreed = 'AGREED'
    verified = 'VERIFIED'
    finalized = 'FINALIZED'
    terminated = 'TERMINATED'


class LanguageValue(MyBaseModel):
    field_value: Optional[str] = Field(None, alias='@value')
    field_language: Optional[str] = Field(None, alias='@language')


class JsonLd(MyBaseModel):
    field_context: Optional[str] = Field(
        'https://w3id.org/dspace/v0.8/context.json', alias='@context'
    )
    field_id: Optional[str] = Field(None, alias='@id')


class DcatDistribution(MyBaseModel):
    field_type: Optional[str] = Field(None, alias='@type')
    dct_format: Optional[str] = Field(None, alias='dct:format')
    dcat_access_service: Optional[str] = Field(None, alias='dcat:accessService')


class DcatService(MyBaseModel):
    field_id: Optional[str] = Field(None, alias='@id')
    field_type: Optional[str] = Field(None, alias='@type')
    dct_terms: Optional[str] = Field(None, alias='dct:terms')
    dct_endpoint_url: Optional[str] = Field(None, alias='dct:endpointUrl')


class OdrlOperand(MyBaseModel):
    value: Optional[str] = None


class OdrlConstraint(MyBaseModel):
    left_operand: Optional[OdrlOperand] = Field(None, alias='leftOperand')
    right_operand: Optional[OdrlOperand] = Field(None, alias='rightOperand')
    operator: Optional[str] = None


class OdrlRule(MyBaseModel):
    action: Optional[str] = None
    constraint: Optional[OdrlConstraint] = None
    duty: Optional[List[str]] = None


class OdrlPolicy(MyBaseModel):
    field_id: Optional[str] = Field(None, alias='@id')
    permission: Optional[List[OdrlRule]] = None
    prohibition: Optional[List[OdrlRule]] = None
    obligation: Optional[List[OdrlRule]] = None


class OdrlOffer(OdrlPolicy):
    target: Optional[str] = None


class ContractRequestMessage(MyBaseModel):
    field_context: Optional[str] = Field(
        'https://w3id.org/dspace/v0.8/context.json', alias='@context'
    )
    field_id: Optional[str] = Field(None, alias='@id')
    dspace_dataset: Optional[str] = Field(
        None, alias='dspace:dataset', description='@id of the dataset'
    )
    dspace_process_id: Optional[str] = Field(
        None, alias='dspace:processId', description='TODO: Deprecated? To be removed?'
    )
    dspace_offer: Optional[OdrlOffer] = Field(None, alias='dspace:offer')
    dscpace_callback_address: Optional[str] = Field(
        None, alias='dscpace:callbackAddress'
    )


class ContracAgreementVerificationMessage(JsonLd):
    field_type: Optional[str] = Field(
        'dspace:ContractAgreementVerificationMessage', alias='@type'
    )
    dspace_process_id: Optional[str] = Field(None, alias='dspace:processId')


class ContractNegotiationTerminationMessage(JsonLd):
    field_type: Optional[str] = Field(
        'dspace:ContractNegotiationTerminationMessage', alias='@type'
    )
    dspace_process_id: Optional[str] = Field(None, alias='dspace:processId')
    dspace_code: Optional[str] = Field(
        None, alias='dspace:code', description='TODO: not documented?'
    )
    dspace_reason: Optional[List[LanguageValue]] = Field(
        None, alias='dspace:reason', description='TODO: can be a link / @id too'
    )


class ContractNegotiation(JsonLd):
    field_type: Optional[str] = Field(None, alias='@type')
    dscpace_process_id: Optional[str] = Field(None, alias='dscpace:processId')
    dspace_state: Optional[DspaceState] = Field(None, alias='dspace:state')
    dspace_checksum: Optional[str] = Field(
        None, alias='dspace:checksum', description='TODO: not explained anywhere'
    )


class DcatDataset(MyBaseModel):
    field_id: Optional[str] = Field(None, alias='@id')
    field_type: Optional[str] = Field(None, alias='@type')
    dct_title: Optional[str] = Field(None, alias='dct:title')
    dct_description: Optional[str] = Field(None, alias='dct:description')
    dct_keyword: Optional[List[str]] = Field(None, alias='dct:keyword')
    odrl_has_policy: Optional[List[OdrlPolicy]] = Field(None, alias='odrl:hasPolicy')
    dcat_distribution: Optional[DcatDistribution] = Field(
        None, alias='dcat:distribution'
    )


class DcatCatalog(MyBaseModel):
    field_context: Optional[str] = Field(None, alias='@context')
    field_id: Optional[str] = Field(None, alias='@id')
    field_type: Optional[str] = Field(None, alias='@type')
    dct_title: Optional[str] = Field(None, alias='dct:title')
    dct_publisher: Optional[str] = Field(None, alias='dct:publisher')
    dcat_keyword: Optional[List[str]] = Field(None, alias='dcat:keyword')
    dcat_service: Optional[DcatService] = Field(None, alias='dcat:service')
    dcat_dataset: Optional[List[DcatDataset]] = Field(None, alias='dcat:dataset')
