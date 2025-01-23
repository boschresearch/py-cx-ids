from pydantic import BaseModel
from typing import Union, Optional, Callable, Any

from fastapi.encoders import jsonable_encoder

class MyBaseModel(BaseModel):
    """
    Base Model for pydatnic models to properly set the usage of aliases and provide a place for
    'global' configs
    """
    def json(self, exclude_none=True, by_alias = True, exclude_unset = False, **kwargs):
        result = super().dict(exclude_none=exclude_none, by_alias=by_alias, exclude_unset=exclude_unset, **kwargs)
        json_result = jsonable_encoder(result) # converts e.g. datetime to string
        return json_result

    def dict(self, exclude_none=True, by_alias = True, exclude_unset = False, **kwargs):
        """
        Beware: exclude_unset=True also removes default values!
        """
        #exclude_unset = True
        return super().dict(exclude_none=exclude_none, by_alias=by_alias, exclude_unset=exclude_unset, **kwargs)

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True # new in version v2.0 shoould allow field names in constructors
        use_enum_values = True
