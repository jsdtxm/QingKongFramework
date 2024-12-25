from itertools import chain
from typing import List, Optional
from libs.models.base import BaseModel
import inspect
from importlib import import_module
from libs.apps import Apps

def model_object_to_name(model: "BaseModel"):
    return f"{model.app.label}.{model.__name__}"


def model_name_preprocess(model_name: str | BaseModel):
    if isinstance(model_name, str):
        if "." not in model_name:
            package = inspect.stack()[2].frame.f_globals.get("__package__")
            apps: Apps = import_module("libs.apps").apps
            app_config = apps.get_app_config(package)
            
            return f"{app_config.label}.{model_name}"
        
    elif issubclass(model_name, BaseModel):
        return model_object_to_name(model_name)
    
    return model_name


def model_to_dict(
    instance: "BaseModel",
    fields: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
):
    """
    Return a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, return only the
    named.

    ``exclude`` is an optional list of field names. If provided, exclude the
    named from the returned dict, even if they are listed in the ``fields``
    argument.
    """

    opts = instance._meta
    data = {}
    for f in chain(opts.fields, opts.m2m_fields, opts.fk_fields, opts.o2o_fields):
        if fields is not None and f not in fields:
            continue
        if exclude and f in exclude:
            continue
        data[f] = getattr(instance, f)
    return data
