import inspect
from importlib import import_module
from itertools import chain
from typing import List, Optional, Union

from fastapp.apps import Apps
from fastapp.exceptions import Http404
from fastapp.models.exceptions import DoesNotExist
from fastapp.models.model import Model


def model_object_to_name(model: "Model"):
    return f"{model.app.label}.{model.__name__}"


def model_name_preprocess(model_name: Union[str, "Model"]):
    if isinstance(model_name, str):
        # HACK for self-referential models
        if model_name.lower() == "self":
            return "self.Self"
        elif "." not in model_name:
            package = inspect.stack()[2].frame.f_globals.get("__package__")
            apps: Apps = import_module("fastapp.apps").apps
            app_config = apps.get_app_config(package)

            return f"{app_config.label}.{model_name}"

    elif issubclass(model_name, Model):
        return model_object_to_name(model_name)

    return model_name


def model_to_dict(
    instance: "Model",
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
    default_exclude_fields = opts.backward_fk_fields | opts.m2m_fields | opts.fk_fields | opts.o2o_fields
    for f in opts.fields:
        if fields is None and f in default_exclude_fields:
            continue
        if fields is not None and f not in fields:
            continue
        if exclude and f in exclude:
            continue

        value = getattr(instance, f)
        if value is not None and value.__class__.__name__ == "ndarray":
            continue
        data[f] = value
    return data


async def get_object_or_404(model_class, *args, **kwargs):
    try:
        return await model_class.get(*args, **kwargs)
    except DoesNotExist:
        if isinstance(model_class, type):
            name = model_class.__name__
        else:
            name = model_class.__class__.__name__
            if name == "QuerySet":
                name = model_class.model.__name__

        raise Http404("No %s matches the given query." % name)
