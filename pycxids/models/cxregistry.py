from uuid import uuid4
from typing import List, Optional
from pycxids.models.base_model import MyBaseModel
from pydantic import Field, constr
from pycxids.models.generated.registry import GlobalReference


def uuid4_str():
    return str(uuid4())

class CxSubmodelEndpoint(MyBaseModel):
    endpoint_address: constr(min_length=1, max_length=512) = Field(
        ..., alias='endpointAddress'
    )
    semantic_id: str

    # optional - generate if doesn't exist
    identification: Optional[str] = Field(default_factory=uuid4_str)
    id_short: Optional[constr(min_length=1, max_length=100)] = Field(
        alias='idShort',
        default_factory=uuid4_str
    )


class CxAas(MyBaseModel):
    """
    A simplified version of the AAS with values we need in CX
    """
    submodels: List[CxSubmodelEndpoint] = Field(...)

    # optional - generate if doesn't exist
    identification: Optional[str] = Field(default_factory=uuid4_str)
    cxid: Optional[str] = Field(default_factory=uuid4_str)
