from pydantic import BaseModel
from typing import Union, Optional, Callable, Any


class MyBaseModel(BaseModel):
    """
    Base Model for pydatnic models to properly set the usage of aliases and provide a place for
    'global' configs
    """
    def json(self, *, include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None, exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None, by_alias: bool = False, skip_defaults: bool = None, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, encoder: Optional[Callable[[Any], Any]] = None, models_as_dict: bool = True, **dumps_kwargs: Any) -> str:
        by_alias = True
        exclude_unset = True
        return super().json(include=include, exclude=exclude, by_alias=by_alias, skip_defaults=skip_defaults, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults, exclude_none=exclude_none, encoder=encoder, models_as_dict=models_as_dict, **dumps_kwargs)

    def dict(self, *, include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None, exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None, by_alias: bool = False, skip_defaults: bool = None, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False) -> 'DictStrAny':
        by_alias = True
        exclude_unset = True
        return super().dict(include=include, exclude=exclude, by_alias=by_alias, skip_defaults=skip_defaults, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults, exclude_none=exclude_none)

    class Config:
        allow_population_by_field_name = True