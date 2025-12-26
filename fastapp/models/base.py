from collections import defaultdict
from typing import TYPE_CHECKING, Any, List, Literal, Optional, Self, Tuple, Type

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.expressions import Q
from tortoise.fields import relational
from tortoise.models import Model as TortoiseModel
from tortoise.models import ModelMeta as TortoiseModelMeta
from tortoise.queryset import MODEL  # type: ignore

from fastapp import apps
from fastapp.apps.config import AppConfig
from fastapp.models.queryset import QuerySet
from fastapp.utils.functional import classproperty
from fastapp.utils.typing import type_to_str

if TYPE_CHECKING:
    from fastapp.models.info import MetaInfo


class BaseMeta:
    # manager = Manager()   # 先注释掉，观察一下
    external: bool = False
    managed: bool = True
    ignore_schema: Optional[bool] = None
    app: str = "none"
    permissions: List[tuple[str, str] | str] = []


class ModelMetaClass(TortoiseModelMeta):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        module_name: str = attrs.get("__module__", None)
        if module_name and module_name.endswith(".models"):
            meta_class = attrs.get("Meta", type("Meta", (BaseMeta,), {}))
            abstract = getattr(meta_class, "abstract", False)

            if (
                getattr(meta_class, "ignore_schema", None) is None
                and getattr(meta_class, "external", False)
                and not getattr(meta_class, "managed", True)
            ):
                meta_class.ignore_schema = True

            if not abstract:
                app_config = apps.apps.app_configs[module_name.rsplit(".", 1)[0]]
                attrs["app"] = app_config
                meta_class.app = app_config.label
                meta_class.app_config = app_config

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
                    meta_class.table = (
                        f"{app_config.label.replace('.', '_')}_{name.lower()}"
                    )

            attrs["Meta"] = meta_class

        return super().__new__(mcs, name, bases, attrs)


def field_filter(stubgen_meta: "BaseModel.StubGenMeta", fields):
    include, exclude = (
        getattr(stubgen_meta, "include", None),
        getattr(stubgen_meta, "exclude", None),
    )

    if include is None and exclude is None:
        return [x["name"] for x in fields]

    if include == "__all__":
        return [x["name"] for x in fields]

    if exclude == "__all__":
        return []

    filtered_fields = []
    for field in fields:
        if include and field["name"] not in include:
            continue
        if exclude and field["name"] in exclude:
            continue

        filtered_fields.append(field["name"])

    return filtered_fields


def generate_query_params_attrs(
    cls: "BaseModel", mode: Literal["full", "lite"] = "lite", depth=0, max_depth=1
):
    from fastapp.models.fields import data as data_fields

    need_import = defaultdict(set)
    kwargs = []

    global_full = mode == "full"

    for _, fields in filter(
        lambda x: x[0]
        in {"pk_field", "data_fields", "fk_fields", "backward_fk_fields"},
        cls.describe(serializable=False).items(),
    ):
        if not isinstance(fields, list):
            fields = [
                fields,
            ]

        query_extend_fileds = field_filter(cls.StubGenMeta, fields)

        for field in fields:
            field_type = field["field_type"]
            name, ptype = field["name"], field["python_type"]

            field_full = name in getattr(cls.StubGenMeta, "full", [])

            if (
                issubclass(field_type, relational.ForeignKeyFieldInstance)
                or issubclass(field_type, relational.OneToOneFieldInstance)
                or issubclass(field_type, relational.BackwardOneToOneRelation)
                or issubclass(field_type, relational.BackwardFKRelation)
                or issubclass(field_type, relational.ManyToManyFieldInstance)
            ):
                if depth >= max_depth:
                    continue

                if name not in query_extend_fileds:
                    continue

                need_import[ptype.__module__].add(ptype.__name__)

                sub_need_import, sub_kwargs = generate_query_params_attrs(
                    ptype, mode, depth + 1, max_depth
                )

                for k, v in sub_need_import.items():
                    need_import[k].update(v)

                if ptype.__name__ == "User":
                    kwargs.extend([(name, 'typing.Union["User", "UserProtocol"]')])
                else:
                    kwargs.extend([(name, f'"{ptype.__name__}"')])

                kwargs.extend([(f"{name}__{x[0]}", x[1]) for x in sub_kwargs])

            else:
                ptype_str = type_to_str(ptype)

                optional = field.get("nullable") or field.get("default") is not None

                kwargs.append(
                    (
                        name,
                        f"typing.Optional[{ptype_str}]" if optional else ptype_str,
                    ),
                )

                if name not in query_extend_fileds:
                    continue

                if (global_full or field_full) or (
                    ptype_str not in {"datetime.datetime", "float"}
                    and field_type
                    not in [
                        data_fields.TextField,
                    ]
                ):
                    kwargs.append((f"{name}__in", f"typing.Iterable[{ptype_str}]"))

                if global_full or field_full:
                    kwargs.extend(
                        [
                            (f"{name}__exact", ptype_str),
                            (f"{name}__iexact", ptype_str),
                            (f"{name}__isnull", "bool"),
                        ]
                    )

                if ptype_str in ("int", "float", "datetime.datetime"):
                    if (
                        (global_full or field_full)
                        or name
                        not in {
                            "id",
                        }
                        and not name.endswith("_id")
                    ):
                        kwargs.extend(
                            [
                                (f"{name}__{x}", ptype_str)
                                for x in ["gt", "gte", "lt", "lte"]
                            ]
                        )
                    if global_full or field_full:
                        kwargs.append((f"{name}__range", Tuple[ptype, ptype]))
                if ptype_str == "str":
                    if (global_full or field_full) or name not in {"uuid"}:
                        kwargs.extend(
                            [
                                (f"{name}__{x}", ptype_str)
                                for x in [
                                    "contains",
                                    "icontains",
                                    "startswith",
                                    "endswith",
                                ]
                            ]
                        )
                    if global_full or field_full:
                        kwargs.extend(
                            [
                                (f"{name}__{x}", ptype_str)
                                for x in [
                                    "istartswith",
                                    "iendswith",
                                ]
                            ]
                        )
                if (global_full or field_full) and ptype_str == "datetime.datetime":
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
    @classproperty
    def objects(cls):
        return cls._meta.manager

    app: AppConfig

    if TYPE_CHECKING:
        _meta: "MetaInfo"

        @classmethod
        def all(
            cls, using_db: Optional[BaseDBAsyncClient] = None
        ) -> QuerySet[Self]: ...

        @classmethod
        def filter(cls, *args: Q, **kwargs: Any) -> QuerySet[Self]: ...

        @classmethod
        @property
        def objects(cls) -> Type[Self]: ...

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    # Allow generic typing checking for generic views.
    def __class_getitem__(cls, *args, **kwargs):
        return cls

    @classmethod
    def generate_query_params(cls, mode: Literal["full", "lite"] = "lite"):
        need_import, kwargs = generate_query_params_attrs(cls, mode)

        create_params_code = "class CreateParams(typing.TypedDict, total=False):\n"
        query_params_code = "class QueryParams(CreateParams, total=False):\n"

        create_flag, query_flag = False, False
        for arg in kwargs:
            if "__" not in arg[0]:
                create_flag = True
                create_params_code += f"    {arg[0]}: {arg[1]}\n"
            else:
                query_flag = True
                query_params_code += f"    {arg[0]}: {arg[1]}\n"

        if not create_flag:
            create_params_code += "    pass\n"

        if not query_flag:
            query_params_code += "    pass\n"

        return need_import, create_params_code + "\n" + query_params_code

    class Meta(BaseMeta):
        pass

    class PydanticMeta:
        include = ()
        exclude = ()
        max_recursion = 1

    class StubGenMeta:
        include = "__all__"  # '__all__'|('field_name', )
        exclude = ()
        full = ()
