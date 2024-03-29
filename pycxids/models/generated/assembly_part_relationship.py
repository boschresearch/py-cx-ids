# generated by datamodel-codegen:
#   filename:  assemblypartrelationship_1.1.1.yaml
#   timestamp: 2023-03-31T20:58:28+00:00

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pycxids.models.base_model import MyBaseModel
from pydantic import Field, constr


class Error(MyBaseModel):
    message: Optional[constr(min_length=1)] = None
    path: Optional[constr(min_length=1)] = None
    details: Dict[str, Dict[str, Any]]
    code: Optional[str] = None


class QuantityCharacteristic(MyBaseModel):
    quantity_number: float = Field(
        ...,
        alias='quantityNumber',
        description='Quantifiable number of objects in reference to the measurementUnit',
    )
    measurement_unit: constr(regex=r'[a-zA-Z]*:[a-zA-Z]+') = Field(
        ...,
        alias='measurementUnit',
        description='Describes a Property containing a reference to one of the units in the Unit Catalog.',
    )


class LifecycleContextCharacteristic(Enum):
    as_required = 'AsRequired'
    as_designed = 'AsDesigned'
    as_planned = 'AsPlanned'
    as_built = 'AsBuilt'
    as_maintained = 'AsMaintained'
    as_recycled = 'AsRecycled'


class ChildData(MyBaseModel):
    created_on: constr(
        regex=r'-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?'
    ) = Field(
        ...,
        alias='createdOn',
        description='Describes a Property which contains the date and time with an optional timezone.',
    )
    quantity: QuantityCharacteristic
    last_modified_on: Optional[
        constr(
            regex=r'-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?'
        )
    ] = Field(
        None,
        alias='lastModifiedOn',
        description='Describes a Property which contains the date and time with an optional timezone.',
    )
    lifecycle_context: LifecycleContextCharacteristic = Field(
        ..., alias='lifecycleContext'
    )
    child_catena_x_id: constr(
        regex=r'(^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$)|(^urn:uuid:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$)'
    ) = Field(
        ...,
        alias='childCatenaXId',
        description='The provided regular expression ensures that the UUID is composed of five groups of characters separated by hyphens, in the form 8-4-4-4-12 for a total of 36 characters (32 hexadecimal characters and 4 hyphens), optionally prefixed by "urn:uuid:" to make it an IRI.',
    )


class AssemblyPartRelationship(MyBaseModel):
    catena_x_id: constr(
        regex=r'(^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$)|(^urn:uuid:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$)'
    ) = Field(
        ...,
        alias='catenaXId',
        description='The provided regular expression ensures that the UUID is composed of five groups of characters separated by hyphens, in the form 8-4-4-4-12 for a total of 36 characters (32 hexadecimal characters and 4 hyphens), optionally prefixed by "urn:uuid:" to make it an IRI.',
    )
    child_parts: List[ChildData] = Field(
        ...,
        alias='childParts',
        description='Set of child parts the parent object is assembled by (one structural level down).',
    )


class ErrorResponse(MyBaseModel):
    error: Error


class PagingSchema(MyBaseModel):
    items: Optional[List[AssemblyPartRelationship]] = None
    total_items: Optional[float] = Field(None, alias='totalItems')
    total_pages: Optional[float] = Field(None, alias='totalPages')
    page_size: Optional[float] = Field(None, alias='pageSize')
    current_page: Optional[float] = Field(None, alias='currentPage')
