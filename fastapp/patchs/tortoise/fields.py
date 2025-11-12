from functools import partial
from typing import Any, List, Optional, Set, Type, Union

from tortoise.exceptions import (
    ConfigurationError,
    OperationalError,
)


def describe(self, serializable: bool) -> dict:
    def _type_name(typ: Type) -> str:
        if typ.__module__ == "builtins":
            return typ.__name__
        if typ.__module__ == "typing":
            return str(typ).replace("typing.", "")
        return f"{typ.__module__}.{typ.__name__}"

    def type_name(typ: Any) -> Union[str, List[str]]:
        try:
            return typ._meta.full_name
        except (AttributeError, TypeError):
            pass
        try:
            return _type_name(typ)
        except AttributeError:
            try:
                return [_type_name(_typ) for _typ in typ]  # pragma: nobranch
            except TypeError:
                return str(typ)

    def default_name(default: Any) -> Optional[Union[int, float, str, bool]]:
        if isinstance(default, (int, float, str, bool, type(None))):
            return default
        if isinstance(default, partial):
            return str(default)
        if callable(default):
            return f"<function {default.__module__}.{default.__name__}>"
        return str(default)

    field_type = getattr(self, "related_model", self.field_type)
    desc = {
        "name": self.model_field_name,
        "field_type": self.__class__.__name__ if serializable else self.__class__,
        "db_column": self.source_field or self.model_field_name,
        "python_type": type_name(field_type) if serializable else field_type,
        "generated": self.generated,
        "nullable": self.null,
        "unique": self.unique,
        "indexed": self.index or self.unique,
        "default": default_name(self.default) if serializable else self.default,
        "description": self.description,
        "docstring": self.docstring,
        "constraints": self.constraints,
    }

    if self.has_db_field:
        desc["db_field_types"] = self.get_db_field_types()

    return desc


def _set_kwargs(self, kwargs: dict) -> Set[str]:
    meta = self._meta

    # Assign values and do type conversions
    passed_fields = {*kwargs.keys()} | meta.fetch_fields

    for key, value in kwargs.items():
        if key in meta.fk_fields or key in meta.o2o_fields:
            if value and not value._saved_in_db:
                raise OperationalError(
                    f"You should first call .save() on {value} before referring to it"
                )
            setattr(self, key, value)
            passed_fields.add(meta.fields_map[key].source_field)
        elif key in meta.fields_db_projection:
            field_object = meta.fields_map[key]
            if field_object.pk and field_object.generated:
                self._custom_generated_pk = True
            if value is None:
                if field_object.default is not None:
                    value = field_object.default
                elif not field_object.null:
                    raise ValueError(
                        f"{key} is non nullable field, but null was passed"
                    )
            setattr(self, key, field_object.to_python_value(value))
        elif key in meta.backward_fk_fields:
            raise ConfigurationError(
                "You can't set backward relations through init, change related model instead"
            )
        elif key in meta.backward_o2o_fields:
            raise ConfigurationError(
                "You can't set backward one to one relations through init,"
                " change related model instead"
            )
        elif key in meta.m2m_fields:
            raise ConfigurationError(
                "You can't set m2m relations through init, use m2m_manager instead"
            )

    return passed_fields


from tortoise import models
from tortoise.fields import base

base.Field.describe = describe
models.Model._set_kwargs = _set_kwargs
