# generated by datamodel-codegen:
#   filename:  http_binding_openapi.yaml
#   timestamp: 2024-03-06T15:13:00+00:00

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Union

from pycxids.models.base_model import MyBaseModel
from pydantic import Field


class DspaceFilter(MyBaseModel):
    pass


class DspaceEventType(str, Enum):
    https___w3id_org_dspace_v0_8_finalized = 'https://w3id.org/dspace/v0.8/FINALIZED'
    https___w3id_org_dspace_v0_8_accepted = 'https://w3id.org/dspace/v0.8/ACCEPTED'
    https___w3id_org_dspace_v0_8_terminated = 'https://w3id.org/dspace/v0.8/TERMINATED'


class NegotiationState(str, Enum):
    requested = 'REQUESTED'
    offered = 'OFFERED'
    accepted = 'ACCEPTED'
    agreed = 'AGREED'
    verified = 'VERIFIED'
    finalized = 'FINALIZED'
    terminated = 'TERMINATED'


class TransferState(str, Enum):
    requested = 'REQUESTED'
    started = 'STARTED'
    terminated = 'TERMINATED'
    completed = 'COMPLETED'
    suspended = 'SUSPENDED'


class LanguageValue(MyBaseModel):
    field_value: Optional[str] = Field(None, alias='@value')
    field_language: Optional[str] = Field(None, alias='@language')


class FieldContext(MyBaseModel):
    pass


class JsonLd(MyBaseModel):
    field_context: Optional[Union[List[str], FieldContext]] = Field(
        {
            'dct': 'https://purl.org/dc/terms/',
            'tx': 'https://w3id.org/tractusx/v0.0.1/ns/',
            'edc': 'https://w3id.org/edc/v0.0.1/ns/',
            'dcat': 'https://www.w3.org/ns/dcat/',
            'odrl': 'http://www.w3.org/ns/odrl/2/',
            'dspace': 'https://w3id.org/dspace/v0.8/',
        },
        alias='@context',
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


class OdrlOperator(MyBaseModel):
    field_id: Optional[str] = Field(None, alias='@id')


class OdrlConstraint(MyBaseModel):
    field_type: Optional[str] = Field(None, alias='@type')
    odrl_left_operand: Optional[str] = Field(None, alias='odrl:leftOperand')
    odrl_operator: Optional[Union[str, OdrlOperator]] = Field(
        None, alias='odrl:operator'
    )
    odrl_right_operand: Optional[str] = Field(None, alias='odrl:rightOperand')


class OdrlLogicalConstraint(MyBaseModel):
    field_id: Optional[str] = Field(None, alias='@id')
    field_type: Optional[str] = Field('LogicalConstraint', alias='@type')
    odrl_and: Optional[Union[OdrlConstraint, List[OdrlConstraint]]] = Field(
        None, alias='odrl:and'
    )
    odrl_or: Optional[List[OdrlConstraint]] = Field(None, alias='odrl:or')


class Action(MyBaseModel):
    odrl_type: Optional[str] = Field(None, alias='odrl:type')


class OdrlRule(MyBaseModel):
    odrl_action: Union[str, Action] = Field(..., alias='odrl:action')
    odrl_constraint: Optional[
        Union[OdrlLogicalConstraint, OdrlConstraint, List[OdrlConstraint]]
    ] = Field(None, alias='odrl:constraint')


class OdrlPermission(OdrlRule):
    odrl_target: Optional[str] = Field(
        None,
        alias='odrl:target',
        description='ODRL requires this. DSP did remove it (MUST NOT) and is thinking about to get it back in again. EDC also requires it.',
    )


class OdrlPolicy(MyBaseModel):
    field_id: Optional[str] = Field(None, alias='@id')
    field_type: Optional[str] = Field('odrl:Policy', alias='@type')
    odrl_profile: Optional[str] = Field(None, alias='odrl:profile')
    odrl_permission: Optional[Union[OdrlPermission, List[OdrlPermission]]] = Field(
        None, alias='odrl:permission'
    )
    odrl_prohibition: Optional[Union[OdrlRule, List[OdrlRule]]] = Field(
        None, alias='odrl:prohibition'
    )
    odrl_obligation: Optional[Union[OdrlRule, List[OdrlRule]]] = Field(
        None, alias='odrl:obligation'
    )


class OdrlOffer(OdrlPolicy):
    field_type: Optional[str] = Field('odrl:Offer', alias='@type')
    odrl_target: Optional[str] = Field(
        None,
        alias='odrl:target',
        description='This is used in EDC, but according to DSP model, this should be removed',
    )


class DspaceTimestamp(MyBaseModel):
    field_type: Optional[str] = Field('xsd:dateTime', alias='@type')
    field_value: Optional[str] = Field(None, alias='@value')


class CatalogRequestMessage(JsonLd):
    field_type: Optional[str] = Field('dspace:CatalogRequestMessage', alias='@type')
    filter: Optional[DspaceFilter] = None


class ContractRequestMessage(JsonLd):
    field_type: Optional[str] = Field('dspace:ContractRequestMessage', alias='@type')
    dspace_dataset: Optional[str] = Field(
        None, alias='dspace:dataset', description='@id of the dataset'
    )
    dspace_data_set: Optional[str] = Field(
        None,
        alias='dspace:dataSet',
        description='Only there for compatibility reasons. Seems to be a type in the spec',
    )
    dspace_process_id: Optional[str] = Field(
        None, alias='dspace:processId', description='TODO: Deprecated? To be removed?'
    )
    dspace_offer: Optional[OdrlOffer] = Field(None, alias='dspace:offer')
    dspace_callback_address: Optional[str] = Field(None, alias='dspace:callbackAddress')


class ContractNegotiationEventMessage(JsonLd):
    field_type: Optional[str] = Field(
        'dspace:ContractNegotiationEventMessage', alias='@type'
    )
    dspace_process_id: Optional[str] = Field(None, alias='dspace:processId')
    dspace_event_type: Optional[DspaceEventType] = Field(None, alias='dspace:eventType')


class ContractAgreementVerificationMessage(JsonLd):
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


class ContractOfferMessage(JsonLd):
    field_type: Optional[str] = Field('dspace:ContractOfferMessage', alias='@type')
    dspace_process_id: Optional[str] = Field(None, alias='dspace:processId')
    dspace_offer: Optional[OdrlOffer] = Field(None, alias='dspace:offer')
    dspace_callback_address: Optional[str] = Field(None, alias='dspace:callbackAddress')


class ContractNegotiation(JsonLd):
    field_type: Optional[str] = Field('dspace:ContractNegotiation', alias='@type')
    dspace_process_id: Optional[str] = Field(None, alias='dspace:processId')
    dspace_state: Optional[TransferState] = Field(None, alias='dspace:state')


class TransferRequestMessage(JsonLd):
    field_type: Optional[str] = Field('dspace:TransferRequestMessage', alias='@type')
    dspace_agreement_id: Optional[str] = Field(
        None,
        alias='dspace:agreementId',
        description='The agreementId property refers to an existing contract agreement between the consumer and provider.',
    )
    dct_format: Optional[str] = Field(
        None,
        alias='dct:format',
        description='The dct:format property is a format specified by a Distribution for the Asset associated with the agreement. This is generally obtained from the provider Catalog.',
    )
    dspace_data_address: Optional[str] = Field(
        None,
        alias='dspace:dataAddress',
        description='The dataAddress property must only be provided if the dct:format requires a push transfer.',
    )
    dspace_callback_address: Optional[str] = Field(None, alias='dspace:callbackAddress')
    dspace_process_id: Optional[str] = Field(
        None, alias='dspace:processId', description='This is an EDC workaround'
    )


class TransferStartMessage(JsonLd):
    field_type: Optional[str] = Field('dspace:TransferStartMessage', alias='@type')
    dspace_process_id: Optional[str] = Field(None, alias='dspace:processId')
    dspace_data_address: Optional[Union[Dict[str, str], str]] = Field(
        None, alias='dspace:dataAddress'
    )


class TransferProcess(JsonLd):
    field_type: Optional[str] = Field('dspace:TransferProcess', alias='@type')
    dspace_process_id: Optional[str] = Field(None, alias='dspace:processId')
    dspace_state: Optional[TransferState] = Field(None, alias='dspace:state')


class DcatDataset(MyBaseModel):
    field_id: Optional[str] = Field(None, alias='@id')
    field_type: Optional[str] = Field('dcat:Dataset', alias='@type')
    dct_title: Optional[str] = Field(None, alias='dct:title')
    dct_description: Optional[str] = Field(None, alias='dct:description')
    dct_keyword: Optional[List[str]] = Field(None, alias='dct:keyword')
    odrl_has_policy: Optional[List[OdrlPolicy]] = Field(None, alias='odrl:hasPolicy')
    dcat_distribution: Optional[DcatDistribution] = Field(
        None, alias='dcat:distribution'
    )


class DcatCatalog(JsonLd):
    field_type: Optional[str] = Field('dcat:Catalog', alias='@type')
    dct_title: Optional[str] = Field(None, alias='dct:title')
    dct_publisher: Optional[str] = Field(None, alias='dct:publisher')
    dcat_keyword: Optional[List[str]] = Field(None, alias='dcat:keyword')
    dcat_service: Optional[DcatService] = Field(None, alias='dcat:service')
    dcat_dataset: Optional[List[DcatDataset]] = Field([], alias='dcat:dataset')


class OdrlAgreement(OdrlPolicy):
    field_type: Optional[str] = Field('odrl:Agreement', alias='@type')
    odrl_target: Optional[str] = Field(None, alias='odrl:target')
    dspace_timestamp: Optional[Union[DspaceTimestamp, str]] = Field(
        None, alias='dspace:timestamp'
    )
    dspace_consumer_id: Optional[str] = Field(None, alias='dspace:consumerId')
    dspace_provider_id: Optional[str] = Field(None, alias='dspace:providerId')


class ContractAgreementMessage(JsonLd):
    field_type: Optional[str] = Field('dspace:ContractAgreementMessage', alias='@type')
    dspace_process_id: Optional[str] = Field(None, alias='dspace:processId')
    dspace_agreement: Optional[OdrlAgreement] = Field(None, alias='dspace:agreement')
    dspace_callback_address: Optional[str] = Field(None, alias='dspace:callbackAddress')
