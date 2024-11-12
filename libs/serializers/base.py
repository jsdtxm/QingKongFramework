import inspect
from typing import Tuple, Type

from pydantic._internal import _model_construction
from pydantic._internal._decorators import (
    FieldValidatorDecoratorInfo,
    ModelValidatorDecoratorInfo,
    PydanticDescriptorProxy,
)
from tortoise.contrib.pydantic.base import PydanticModel
from tortoise.fields.base import Field

from libs.models.base import BaseModel, ModelMetaClass
from libs.serializers.creator import pydantic_model_creator


class SerializerMetaclass(_model_construction.ModelMetaclass):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        if fields_map := dict(filter(lambda x: isinstance(x[1], Field), attrs.items())):
            validators_map = dict(
                filter(
                    lambda x: isinstance(x[1], PydanticDescriptorProxy)
                    and (
                        isinstance(x[1].decorator_info, ModelValidatorDecoratorInfo)
                        or isinstance(x[1].decorator_info, FieldValidatorDecoratorInfo)
                    ),
                    attrs.items(),
                )
            )

            model = ModelMetaClass(
                name,
                (BaseModel,),
                {
                    **fields_map,
                    "PydanticMeta": type(
                        "PydanticMeta", (), {"include": fields_map.keys()}
                    ),
                },
            )

            try:
                pydantic_model = pydantic_model_creator(
                    model, validators=validators_map
                )
                return pydantic_model
            except Exception as e:
                print("ERROR", e)

        return super().__new__(mcs, name, bases, attrs)


class Serializer(PydanticModel, metaclass=SerializerMetaclass):
    @classmethod
    def describe(cls, serializable: bool = True) -> dict:
        """
        Describes the given list of models or ALL registered models.

        :param serializable:
            ``False`` if you want raw python objects,
            ``True`` for JSON-serializable data. (Defaults to ``True``)

        :return:
            A dictionary containing the model description.

            The base dict has a fixed set of keys that reference a list of fields
            (or a single field in the case of the primary key):

            .. code-block:: python3

                {
                    "name":                 str     # Qualified model name
                    "app":                  str     # 'App' namespace
                    "table":                str     # DB table name
                    "abstract":             bool    # Is the model Abstract?
                    "description":          str     # Description of table (nullable)
                    "docstring":            str     # Model docstring (nullable)
                    "unique_together":      [...]   # List of List containing field names that
                                                    #  are unique together
                    "pk_field":             {...}   # Primary key field
                    "data_fields":          [...]   # Data fields
                    "fk_fields":            [...]   # Foreign Key fields FROM this model
                    "backward_fk_fields":   [...]   # Foreign Key fields TO this model
                    "o2o_fields":           [...]   # OneToOne fields FROM this model
                    "backward_o2o_fields":  [...]   # OneToOne fields TO this model
                    "m2m_fields":           [...]   # Many-to-Many fields
                }

            Each field is specified as defined in :meth:`tortoise.fields.base.Field.describe`
        """
        return {
            "name": cls._meta.full_name,
            "app": cls._meta.app,
            "table": cls._meta.db_table,
            "abstract": cls._meta.abstract,
            "description": cls._meta.table_description or None,
            "docstring": inspect.cleandoc(cls.__doc__ or "") or None,
            "unique_together": cls._meta.unique_together or [],
            "indexes": cls._meta.indexes or [],
            "pk_field": cls._meta.fields_map[cls._meta.pk_attr].describe(serializable),
            "data_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name != cls._meta.pk_attr
                and name in (cls._meta.fields - cls._meta.fetch_fields)
            ],
            "fk_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name in cls._meta.fk_fields
            ],
            "backward_fk_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name in cls._meta.backward_fk_fields
            ],
            "o2o_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name in cls._meta.o2o_fields
            ],
            "backward_o2o_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name in cls._meta.backward_o2o_fields
            ],
            "m2m_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name in cls._meta.m2m_fields
            ],
        }
