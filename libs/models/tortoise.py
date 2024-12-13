from copy import deepcopy
from typing import Tuple, Type, Union, cast

from tortoise import Tortoise as RawTortoise
from tortoise.exceptions import ConfigurationError
from tortoise.filters import get_m2m_filters
from tortoise.models import Model

from libs.models.fields.relational import (
    BackwardFKRelation,
    BackwardOneToOneRelation,
    ForeignKeyFieldInstance,
    ManyToManyFieldInstance,
    OneToOneFieldInstance,
)


class Tortoise(RawTortoise):
    @classmethod
    def _init_relations(cls) -> None:
        def get_related_model(
            related_app_name: str, related_model_name: str
        ) -> Type["Model"]:
            """
            Test, if app and model really exist. Throws a ConfigurationError with a hopefully
            helpful message. If successful, returns the requested model.

            :raises ConfigurationError: If no such app exists.
            """
            try:
                return cls.apps[related_app_name][related_model_name]
            except KeyError:
                if related_app_name not in cls.apps:
                    raise ConfigurationError(
                        f"No app with name '{related_app_name}' registered."
                        f" Please check your model names in ForeignKeyFields"
                        f" and configurations."
                    )
                raise ConfigurationError(
                    f"No model with name '{related_model_name}' registered in"
                    f" app '{related_app_name}'."
                )

        def split_reference(reference: str) -> Tuple[str, str]:
            """
            Validate, if reference follow the official naming conventions. Throws a
            ConfigurationError with a hopefully helpful message. If successful,
            returns the app and the model name.

            :raises ConfigurationError: If reference is invalid.
            """
            if len(items := reference.split(".")) != 2:  # pragma: nocoverage
                raise ConfigurationError(
                    f"'{reference}' is not a valid model reference Bad Reference."
                    " Should be something like '<appname>.<modelname>'."
                )
            return items[0], items[1]

        def init_fk_o2o_field(model: Type["Model"], field: str, is_o2o=False) -> None:
            if is_o2o:
                fk_object: Union[OneToOneFieldInstance, ForeignKeyFieldInstance] = cast(
                    OneToOneFieldInstance, model._meta.fields_map[field]
                )
            else:
                fk_object = cast(ForeignKeyFieldInstance, model._meta.fields_map[field])
            related_app_name, related_model_name = split_reference(fk_object.model_name)
            related_model = get_related_model(related_app_name, related_model_name)

            if to_field := fk_object.to_field:
                related_field = related_model._meta.fields_map.get(to_field)
                if not related_field:
                    raise ConfigurationError(
                        f'there is no field named "{to_field}" in model "{related_model_name}"'
                    )
                if not related_field.unique:
                    raise ConfigurationError(
                        f'field "{to_field}" in model "{related_model_name}" is not unique'
                    )
            else:
                fk_object.to_field = related_model._meta.pk_attr
                related_field = related_model._meta.pk
            key_fk_object = deepcopy(related_field)
            fk_object.to_field_instance = related_field  # type:ignore[arg-type,call-overload]
            fk_object.field_type = fk_object.to_field_instance.field_type

            key_field = fk_object.source_field or f"{field}_id"
            key_fk_object.reference = fk_object
            key_fk_object.source_field = fk_object.source_field or key_field
            for attr in ("index", "default", "null", "generated", "description"):
                setattr(key_fk_object, attr, getattr(fk_object, attr))
            if is_o2o:
                key_fk_object.pk = fk_object.pk
                key_fk_object.unique = fk_object.unique
            else:
                key_fk_object.pk = False
                key_fk_object.unique = False
            if key_field not in model._meta.fields_map:
                model._meta.add_field(key_field, key_fk_object)
            fk_object.related_model = related_model
            fk_object.source_field = key_field
            if (backward_relation_name := fk_object.related_name) is not False:
                if not backward_relation_name:
                    backward_relation_name = f"{model._meta.db_table}s"
                if backward_relation_name in related_model._meta.fields:
                    raise ConfigurationError(
                        f'backward relation "{backward_relation_name}" duplicates in'
                        f" model {related_model_name}"
                    )
                if is_o2o:
                    fk_relation: Union[BackwardOneToOneRelation, BackwardFKRelation] = (
                        BackwardOneToOneRelation(
                            model,
                            key_field,
                            key_fk_object.source_field,
                            null=True,
                            description=fk_object.description,
                        )
                    )
                else:
                    fk_relation = BackwardFKRelation(
                        model,
                        key_field,
                        key_fk_object.source_field,
                        null=fk_object.null,
                        description=fk_object.description,
                    )
                fk_relation.to_field_instance = fk_object.to_field_instance  # type:ignore
                related_model._meta.add_field(backward_relation_name, fk_relation)
            if is_o2o and fk_object.pk:
                model._meta.pk_attr = key_field

        for app_name, app in cls.apps.items():
            for model_name, model in app.items():
                if model._meta._inited:
                    continue
                model._meta._inited = True
                if not model._meta.db_table:
                    model._meta.db_table = model.__name__.lower()

                for field in sorted(model._meta.fk_fields):
                    init_fk_o2o_field(model, field)

                for field in model._meta.o2o_fields:
                    init_fk_o2o_field(model, field, is_o2o=True)

                for field in list(model._meta.m2m_fields):
                    m2m_object = cast(
                        ManyToManyFieldInstance, model._meta.fields_map[field]
                    )
                    if m2m_object._generated:
                        continue
                    backward_key = m2m_object.backward_key
                    if not backward_key:
                        backward_key = f"{model._meta.db_table}_id"
                        if backward_key == m2m_object.forward_key:
                            backward_key = f"{model._meta.db_table}_rel_id"
                        m2m_object.backward_key = backward_key

                    reference = m2m_object.model_name
                    related_app_name, related_model_name = split_reference(reference)
                    related_model = get_related_model(
                        related_app_name, related_model_name
                    )

                    m2m_object.related_model = related_model

                    backward_relation_name = m2m_object.related_name
                    if not backward_relation_name:
                        backward_relation_name = m2m_object.related_name = (
                            f"{model._meta.db_table}s"
                        )
                    if backward_relation_name in related_model._meta.fields:
                        raise ConfigurationError(
                            f'backward relation "{backward_relation_name}" duplicates in'
                            f" model {related_model_name}"
                        )

                    if not m2m_object.through:
                        related_model_table_name = (
                            related_model._meta.db_table
                            or related_model.__name__.lower()
                        )
                        m2m_object.through = (
                            f"{model._meta.db_table}_{related_model_table_name}"
                        )

                    m2m_relation = ManyToManyFieldInstance(
                        f"{app_name}.{model_name}",
                        m2m_object.through,
                        forward_key=m2m_object.backward_key,
                        backward_key=m2m_object.forward_key,
                        related_name=field,
                        field_type=model,
                        description=m2m_object.description,
                    )
                    m2m_relation._generated = True
                    model._meta.filters.update(get_m2m_filters(field, m2m_object))
                    related_model._meta.add_field(backward_relation_name, m2m_relation)
