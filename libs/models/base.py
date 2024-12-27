from collections import defaultdict
from datetime import datetime
from typing import Any, Generic, Literal, Optional, Self, Tuple, Type

from tortoise.fields import relational
from tortoise.manager import Manager as TortoiseManager
from tortoise.models import Model as TortoiseModel
from tortoise.models import ModelMeta as TortoiseModelMeta
from tortoise.queryset import MODEL
from tortoise.queryset import QuerySet as TortoiseQuerySet

from libs import apps
from libs.apps.config import AppConfig


class Manager(Generic[MODEL], TortoiseManager):
    _model: TortoiseModel
    _queryset_class: Type["QuerySet"] = TortoiseQuerySet

    def __init__(self, model=None) -> None:
        self._model = model

    @classmethod
    def from_queryset(cls, queryset_class, class_name=None):
        if class_name is None:
            class_name = "%sFrom%s" % (cls.__name__, queryset_class.__name__)
        return type(
            class_name,
            (cls,),
            {
                "_queryset_class": queryset_class,
            },
        )

    def create(self, *args, **kwargs):
        return self._model.create(*args, **kwargs)

    def get_queryset(self) -> TortoiseQuerySet[MODEL]:
        return self._queryset_class(self._model)


class QuerySet(TortoiseQuerySet):
    @classmethod
    def as_manager(cls):
        manager = Manager.from_queryset(cls)()
        return manager


class BaseMeta:
    manager = Manager()
    external: bool = False
    ignore_schema: Optional[bool] = None
    app: str = "none"


class ModelMetaClass(TortoiseModelMeta):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        module_name: str = attrs.get("__module__", None)
        if module_name and module_name.endswith(".models"):
            meta_class = attrs.get("Meta", type("Meta", (BaseMeta,), {}))
            abstract = getattr(meta_class, "abstract", False)

            if getattr(meta_class, "ignore_schema", None) is None and getattr(
                meta_class, "external", False
            ):
                meta_class.ignore_schema = True

            if not abstract:
                app_config = apps.apps.app_configs[module_name.rsplit(".", 1)[0]]
                attrs["app"] = app_config
                meta_class.app = app_config.label   # ?
                meta_class.app_config = app_config.label

                if getattr(meta_class, "verbose_name", None) is None:
                    meta_class.verbose_name = name.lower()
                    if getattr(meta_class, "verbose_name_plural", None) is None:
                        meta_class.verbose_name_plural = meta_class.verbose_name

            table = getattr(meta_class, "table", None)
            if table is None:
                db_table = getattr(meta_class, "db_table", None)
                if db_table:
                    meta_class.table = db_table
                elif not abstract:
                    meta_class.table = f"{app_config.label.replace(".", "_")}_{name.lower()}"

            attrs["Meta"] = meta_class

        return super().__new__(mcs, name, bases, attrs)


def generate_query_params_attrs(
    cls: "BaseModel", mode: Literal["full", "lite"] = "lite", depth=0, max_depth=1
):
    need_import = defaultdict(set)
    kwargs = []

    full = mode == "full"

    for _, fields in filter(
        lambda x: x[0]
        in {"pk_field", "data_fields", "fk_fields", "backward_fk_fields"},
        cls.describe(serializable=False).items(),
    ):
        if not isinstance(fields, list):
            fields = [
                fields,
            ]
        for field in fields:
            field_type = field["field_type"]
            name, ptype = field["name"], field["python_type"]

            if (
                field_type is relational.ForeignKeyFieldInstance
                or field_type is relational.OneToOneFieldInstance
                or field_type is relational.BackwardOneToOneRelation
                or field_type is relational.BackwardFKRelation
                or field_type is relational.ManyToManyFieldInstance
            ):
                if depth > max_depth:
                    continue

                need_import[ptype.__module__].add(ptype.__name__)

                sub_need_import, sub_kwargs = generate_query_params_attrs(
                    ptype, mode, depth + 1, max_depth
                )

                for k, v in sub_need_import.items():
                    need_import[k].update(v)

                kwargs.extend([(name, f'"{ptype.__name__}"')])
                kwargs.extend([(f"{name}__{x[0]}", x[1]) for x in sub_kwargs])

            else:
                ptype_str = {int: "int", str: "str", datetime: "datetime.datetime"}.get(
                    ptype, str(ptype)
                )

                optional = field.get("nullable") or field.get("default") is not None

                kwargs.extend(
                    [
                        (
                            name,
                            f"typing.Optional[{ptype_str}]" if optional else ptype_str,
                        ),
                        (f"{name}__in", f"typing.Sequence[{ptype_str}]"),
                    ]
                )

                if full:
                    kwargs.extend(
                        [
                            (f"{name}__exact", ptype_str),
                            (f"{name}__iexact", ptype_str),
                            (f"{name}__isnull", "bool"),
                        ]
                    )

                if ptype_str in ("int", "float", "datetime.datetime"):
                    kwargs.extend(
                        [
                            (f"{name}__{x}", ptype_str)
                            for x in ["gt", "gte", "lt", "lte"]
                        ]
                    )
                    if full:
                        kwargs.append((f"{name}__range", Tuple[ptype, ptype]))
                if ptype_str == "str":
                    kwargs.extend(
                        [
                            (f"{name}__{x}", ptype_str)
                            for x in [
                                "contains",
                                "startswith",
                                "endswith",
                            ]
                        ]
                    )
                    if full:
                        kwargs.extend(
                            [
                                (f"{name}__{x}", ptype_str)
                                for x in [
                                    "icontains",
                                    "istartswith",
                                    "iendswith",
                                ]
                            ]
                        )
                if full and ptype_str == "datetime.datetime":
                    kwargs.extend(
                        [
                            (f"{name}__{x}", "int")
                            for x in [
                                "year",
                                "month",
                                "day",
                                "week_day",
                                "hour",
                                "minute",
                                "second",
                            ]
                        ]
                    )

    return need_import, kwargs


class BaseModel(TortoiseModel, metaclass=ModelMetaClass):
    objects: Manager[Self] = Manager()

    app: AppConfig

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def generate_query_params(cls, mode: Literal["full", "lite"] = "lite") -> None:
        template = "class QueryParams(typing.TypedDict, total=False):\n"

        need_import, kwargs = generate_query_params_attrs(cls, mode)

        for arg in kwargs:
            template += f"    {arg[0]}: {arg[1]}\n"

        return need_import, template

    class Meta(BaseMeta):
        pass

    class PydanticMeta:
        include = ()
        exclude = ()
        max_recursion = 1
