from itertools import chain
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from libs.models.base import BaseModel


def model_object_to_name(model: "BaseModel"):
    return f"{model.app.label}.{model.__name__}"


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
