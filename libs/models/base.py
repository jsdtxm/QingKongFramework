from collections import defaultdict
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generator,
    Generic,
    List,
    Literal,
    Optional,
    Self,
    Set,
    Tuple,
    Type,
    Union,
)

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.expressions import Q
from tortoise.fields import relational
from tortoise.filters import FilterInfoDict
from tortoise.manager import Manager as TortoiseManager
from tortoise.models import Model as TortoiseModel
from tortoise.models import ModelMeta as TortoiseModelMeta
from tortoise.queryset import MODEL
from tortoise.queryset import QuerySet as TortoiseQuerySet
from tortoise.queryset import ValuesListQuery as TortoiseValuesListQuery

from libs import apps
from libs.apps.config import AppConfig
from libs.utils.functional import classproperty
from libs.utils.typing import type_to_str

if TYPE_CHECKING:
    from libs.models.info import MetaInfo


async def values_list_to_named(fields_for_select_list, data):
    return [SimpleNamespace(**dict(zip(fields_for_select_list, x))) for x in await data]


class ValuesListQuery(TortoiseValuesListQuery):
    def __init__(
        self,
        model: Type[MODEL],
        db: BaseDBAsyncClient,
        q_objects: List[Q],
        single: bool,
        raise_does_not_exist: bool,
        fields_for_select_list: Union[Tuple[str, ...], List[str]],
        limit: Optional[int],
        offset: Optional[int],
        distinct: bool,
        orderings: List[Tuple[str, str]],
        flat: bool,
        named: bool,
        annotations: Dict[str, Any],
        custom_filters: Dict[str, FilterInfoDict],
        group_bys: Tuple[str, ...],
        force_indexes: Set[str],
        use_indexes: Set[str],
    ) -> None:
        super().__init__(
            model,
            db,
            q_objects,
            single,
            raise_does_not_exist,
            fields_for_select_list,
            limit,
            offset,
            distinct,
            orderings,
            flat,
            annotations,
            custom_filters,
            group_bys,
            force_indexes,
            use_indexes,
        )
        self.named = named

    def __await__(self) -> Generator[Any, None, Union[List[Any], Tuple[Any, ...]]]:
        if self._db is None:
            self._db = self._choose_db()  # type: ignore
        self._make_query()
        data = self._execute()  # pylint: disable=E1101

        if self.named:
            return values_list_to_named(self.fields_for_select_list, data).__await__()

        return data.__await__()


class QuerySet(TortoiseQuerySet[MODEL]):
    @classmethod
    def as_manager(cls):
        manager = Manager.from_queryset(cls)()
        return manager

    def values_list(
        self, *fields_: str, flat: bool = False, named: bool = False
    ) -> "ValuesListQuery[Literal[False]]":
        """
        Make QuerySet returns list of tuples for given args instead of objects.

        If call after `.get()`, `.get_or_none()` or `.first()` return tuples for given args instead of object.

        If ```flat=True`` and only one arg is passed can return flat list or just scalar.

        If no arguments are passed it will default to a tuple containing all fields
        in order of declaration.
        """
        # HACK change response class
        fields_for_select_list = fields_ or [
            field
            for field in self.model._meta.fields_map
            if field in self.model._meta.db_fields
        ] + list(self._annotations.keys())
        return ValuesListQuery(
            db=self._db,
            model=self.model,
            q_objects=self._q_objects,
            single=self._single,
            raise_does_not_exist=self._raise_does_not_exist,
            flat=flat,
            named=named,
            fields_for_select_list=fields_for_select_list,
            distinct=self._distinct,
            limit=self._limit,
            offset=self._offset,
            orderings=self._orderings,
            annotations=self._annotations,
            custom_filters=self._custom_filters,
            group_bys=self._group_bys,
            force_indexes=self._force_indexes,
            use_indexes=self._use_indexes,
        )

    if TYPE_CHECKING:

        def create(self, *args, **kwargs) -> MODEL: ...

        def filter(self, *args: Q, **kwargs: Any) -> "Self[MODEL]": ...

        def exclude(self, *args: Q, **kwargs: Any) -> "Self[MODEL]": ...

        def order_by(self, *orderings: str) -> "Self[MODEL]": ...

        def offset(self, offset: int) -> "Self[MODEL]": ...

        def limit(self, limit: int) -> "Self[MODEL]": ...


class Manager(Generic[MODEL], TortoiseManager):
    _model: "BaseModel"
    _queryset_class: Type["QuerySet"] = QuerySet

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

    async def create(self, *args, **kwargs):
        return await self._model.create(*args, **kwargs)

    async def get_or_create(self, *args, **kwargs):
        return await self._model.get_or_create(*args, **kwargs)

    def get_queryset(self) -> QuerySet[MODEL]:
        return self._queryset_class(self._model)

    if TYPE_CHECKING:

        def all(self) -> "QuerySet[MODEL]": ...

        @classmethod
        def filter(cls, *args: Q, **kwargs: Any) -> QuerySet[Self]: ...


class BaseMeta:
    # manager = Manager()   # 先注释掉，观察一下
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
    from libs.models.fields import data as data_fields

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
                field_type is relational.ForeignKeyFieldInstance
                or field_type is relational.OneToOneFieldInstance
                or field_type is relational.BackwardOneToOneRelation
                or field_type is relational.BackwardFKRelation
                or field_type is relational.ManyToManyFieldInstance
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
                    kwargs.append((f"{name}__in", f"typing.Sequence[{ptype_str}]"))

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
        def filter(cls, *args: Q, **kwargs: Any) -> QuerySet[Self]: ...

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
