from functools import partial
from typing import Any, List, Optional, Type, Union


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


from tortoise.fields import base

base.Field.describe = describe