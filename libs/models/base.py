from datetime import datetime
from typing import Any, Generic, Optional, Self, Sequence, Tuple, Type

from tortoise.manager import Manager as TortoiseManager
from tortoise.models import Model as TortoiseModel
from tortoise.models import ModelMeta as TortoiseModelMeta
from tortoise.queryset import MODEL
from tortoise.queryset import QuerySet as TortoiseQuerySet

from libs import apps
from libs.apps.config import AppConfig


class Manager(Generic[MODEL], TortoiseManager):
    _model: TortoiseModel

    def create(self, *args, **kwargs):
        return self._model.create(*args, **kwargs)

    def get_queryset(self) -> TortoiseQuerySet[MODEL]:
        return TortoiseQuerySet(self._model)


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
                meta_class.app = app_config.label

            table = getattr(meta_class, "table", None)
            if table is None:
                db_table = getattr(meta_class, "db_table", None)
                if db_table:
                    meta_class.table = db_table
                elif not abstract:
                    meta_class.table = f"{app_config.label}_{name.lower()}"

            attrs["Meta"] = meta_class

        return super().__new__(mcs, name, bases, attrs)


class BaseModel(TortoiseModel, metaclass=ModelMetaClass):
    objects: Manager[Self] = Manager()

    app: AppConfig

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def generate_stub(cls) -> None:
        template = "class QueryParams(typing.TypedDict, total=False):\n"

        for _, fields in filter(
            lambda x: x[0] in {"pk_field", "data_fields", "fk_fields"},
            cls.describe().items(),
        ):
            if not isinstance(fields, list):
                fields = [
                    fields,
                ]
            for field in fields:
                if field["field_type"] == "ForeignKeyFieldInstance":
                    continue

                name, ptype_str = field["name"], field["python_type"]
                ptype = {
                    "int": int,
                    "float": float,
                    "str": str,
                    "datetime.datetime": datetime,
                }[ptype_str]
                kwargs = [
                    (name, ptype_str),
                    (f"{name}__in", Sequence[ptype]),
                    (f"{name}__exact", ptype_str),
                    (f"{name}__iexact", ptype_str),
                    (f"{name}__isnull", "bool"),
                ]

                if ptype_str in ("int", "float", "datetime.datetime"):
                    kwargs.extend(
                        [
                            (f"{name}__{x}", ptype_str)
                            for x in ["gt", "gte", "lt", "lte"]
                        ]
                    )
                    kwargs.append((f"{name}__range", Tuple[ptype, ptype]))
                if ptype_str == "str":
                    kwargs.extend(
                        [
                            (f"{name}__{x}", ptype_str)
                            for x in [
                                "contains",
                                "icontains",
                                "startswith",
                                "istartswith",
                                "endswith",
                                "iendswith",
                            ]
                        ]
                    )
                if ptype_str == "datetime.datetime":
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

                for arg in kwargs:
                    template += f"    {arg[0]}: {arg[1]}\n"

        return template

    class Meta(BaseMeta):
        pass

    class PydanticMeta:
        include = ()
        exclude = ()
        max_recursion = 1
