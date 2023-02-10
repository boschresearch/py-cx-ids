# generated by datamodel-codegen:
#   filename:  aas-registry-openapi.yaml
#   timestamp: 2023-02-09T07:56:36+00:00

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pycxids.models.base_model import MyBaseModel
from pydantic import Field, constr


class ProtocolInformation(MyBaseModel):
    endpoint_address: constr(min_length=1, max_length=512) = Field(
        ..., alias='endpointAddress'
    )
    endpoint_protocol: Optional[constr(min_length=1, max_length=50)] = Field(
        None, alias='endpointProtocol'
    )
    endpoint_protocol_version: Optional[constr(min_length=1, max_length=24)] = Field(
        None, alias='endpointProtocolVersion'
    )
    subprotocol: Optional[constr(min_length=1, max_length=50)] = None
    subprotocol_body: Optional[constr(min_length=1, max_length=50)] = Field(
        None, alias='subprotocolBody'
    )
    subprotocol_body_encoding: Optional[constr(min_length=1, max_length=50)] = Field(
        None, alias='subprotocolBodyEncoding'
    )


class AdministrativeInformation(MyBaseModel):
    revision: Optional[str] = None
    version: Optional[str] = None


class LangString(MyBaseModel):
    language: constr(min_length=1, max_length=10)
    text: constr(min_length=1, max_length=500)


class KeyElements(Enum):
    asset_administration_shell = 'AssetAdministrationShell'
    access_permission_rule = 'AccessPermissionRule'
    concept_description = 'ConceptDescription'
    submodel = 'Submodel'
    annotated_relationship_element = 'AnnotatedRelationshipElement'
    basic_event = 'BasicEvent'
    blob = 'Blob'
    capability = 'Capability'
    data_element = 'DataElement'
    file = 'File'
    entity = 'Entity'
    event = 'Event'
    multi_language_property = 'MultiLanguageProperty'
    operation = 'Operation'
    property = 'Property'
    range = 'Range'
    reference_element = 'ReferenceElement'
    relationship_element = 'RelationshipElement'
    submodel_element = 'SubmodelElement'
    submodel_element_list = 'SubmodelElementList'
    submodel_element_struct = 'SubmodelElementStruct'
    view = 'View'
    fragment_reference = 'FragmentReference'


class Error(MyBaseModel):
    message: Optional[constr(min_length=1)] = Field(
        None,
        description='The detailed error message for the exception which occurred.',
        example='size must be between {min} and {max}',
    )
    path: Optional[constr(min_length=1)] = Field(
        None, description='The requested path.'
    )
    details: Dict[str, Dict[str, Any]] = Field(
        ...,
        description='An object with key/value pairs containing additional information about the error.',
    )


class BatchResult(MyBaseModel):
    message: str = Field(
        ..., description='The detailed error message for the exception which occurred.'
    )
    identification: str = Field(..., description='The requested path.')
    status: int = Field(..., description='The status code')


class Endpoint(MyBaseModel):
    interface: str
    protocol_information: ProtocolInformation = Field(..., alias='protocolInformation')


class GlobalReference(MyBaseModel):
    value: List[constr(min_length=1, max_length=200)] = Field(
        ..., max_items=1, min_items=1
    )


class Key(MyBaseModel):
    type: KeyElements
    value: str


class ErrorResponse(MyBaseModel):
    error: Error


class Descriptor(MyBaseModel):
    endpoints: Optional[List[Endpoint]] = Field(None, max_items=10000)


class ModelReference(MyBaseModel):
    keys: List[Key] = Field(..., max_items=10000)


class HasSemantics(MyBaseModel):
    semantic_id: Optional[GlobalReference] = Field(None, alias='semanticId')


class SubmodelDescriptor(Descriptor):
    administration: Optional[AdministrativeInformation] = None
    description: Optional[List[LangString]] = Field(None, max_items=10000)
    id_short: Optional[constr(min_length=1, max_length=100)] = Field(
        None, alias='idShort'
    )
    identification: constr(min_length=1, max_length=200)
    semantic_id: Optional[GlobalReference] = Field(..., alias='semanticId')
    endpoints: List[Endpoint] = Field(..., max_items=10000)


class IdentifierKeyValuePair(HasSemantics):
    key: constr(min_length=1, max_length=200)
    value: constr(min_length=1, max_length=200)
    external_subject_id: Optional[GlobalReference] = Field(
        None, alias='externalSubjectId'
    )


class Query(MyBaseModel):
    asset_ids: Optional[List[IdentifierKeyValuePair]] = Field(
        None, alias='assetIds', max_items=10000
    )


class ShellLookup(MyBaseModel):
    query: Query


class AssetAdministrationShellDescriptor(Descriptor):
    administration: Optional[AdministrativeInformation] = None
    description: Optional[List[LangString]] = Field(None, max_items=10000)
    global_asset_id: Optional[GlobalReference] = Field(None, alias='globalAssetId')
    id_short: constr(min_length=1, max_length=100) = Field(..., alias='idShort')
    identification: constr(min_length=1, max_length=200)
    specific_asset_ids: Optional[List[IdentifierKeyValuePair]] = Field(
        None, alias='specificAssetIds', max_items=10000
    )
    submodel_descriptors: Optional[List[SubmodelDescriptor]] = Field(
        None, alias='submodelDescriptors', max_items=10000
    )


class AssetAdministrationShellDescriptorCollectionBase(MyBaseModel):
    items: List[AssetAdministrationShellDescriptor] = Field(
        ..., max_items=10000, title='Items'
    )


class AssetAdministrationShellDescriptorCollection(
    AssetAdministrationShellDescriptorCollectionBase
):
    total_items: int = Field(..., alias='totalItems', title='Totalitems')
    current_page: int = Field(..., alias='currentPage', title='Currentpage')
    total_pages: int = Field(..., alias='totalPages', title='Totalpages')
    item_count: int = Field(..., alias='itemCount', title='Itemcount')
