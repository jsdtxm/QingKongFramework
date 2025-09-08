from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Literal,
    Optional,
    Self,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

from pypika import Table
from tortoise import connections
from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.exceptions import FieldError
from tortoise.expressions import Q
from tortoise.fields.relational import RelationalField
from tortoise.filters import FilterInfoDict
from tortoise.queryset import MODEL
from tortoise.queryset import QuerySet as TortoiseQuerySet
from tortoise.queryset import ValuesListQuery as TortoiseValuesListQuery


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
    def __init__(self, model: Type[MODEL]) -> None:
        super().__init__(model)
        self._fields_for_exclude: Tuple[str, ...] = ()

    def _clone(self) -> "QuerySet[MODEL]":
        queryset = super()._clone()
        queryset._fields_for_exclude = self._fields_for_exclude
        return queryset

    def _join_table_with_select_related(
        self,
        model: MODEL,
        table: Table,
        field: str,
        forwarded_fields: str,
        path: Iterable[Optional[str]],
    ) -> Tuple[Table, str]:
        if field in model._meta.fields_db_projection and forwarded_fields:
            raise FieldError(
                f'Field "{field}" for model "{model.__name__}" is not relation'
            )

        field_object = cast(RelationalField, model._meta.fields_map.get(field))
        if not field_object:
            raise FieldError(f'Unknown field "{field}" for model "{model.__name__}"')

        table = self._join_table_by_field(table, field, field_object)
        related_fields = field_object.related_model._meta.db_fields
        append_item = (
            field_object.related_model,
            len(related_fields),
            field,
            model,
            path,
        )

        # FEAT: support defer
        related_defer_field = filter(
            lambda x: x.startswith(f"{field}__"), self._fields_for_exclude
        )

        if append_item not in self._select_related_idx:
            self._select_related_idx.append(append_item)
        for related_field in related_fields:
            # FEAT: support defer
            if related_defer_field and related_field in related_defer_field:
                continue
            self.query = self.query.select(
                table[related_field].as_(f"{table.get_table_name()}.{related_field}")
            )
        if forwarded_fields:
            field, __, forwarded_fields_ = forwarded_fields.partition("__")
            self.query = self._join_table_with_select_related(
                model=field_object.related_model,
                table=table,
                field=field,
                forwarded_fields=forwarded_fields_,
                path=(*path, field),
            )
            return self.query
        return self.query

    # def _make_query(self) -> None:
    # TODO

    @classmethod
    def as_manager(cls):
        from fastapp.models.manager import Manager

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

    def using(self, name: str) -> "QuerySet[MODEL]":
        return self.using_db(connections.get(name))

    def defer(self, *fields_for_exclude: str) -> "QuerySet[MODEL]":
        """
        Fetch EXCLUDE the specified fields to create a partial model.
        """
        queryset = self._clone()
        queryset._fields_for_exclude = fields_for_exclude
        return queryset

    if TYPE_CHECKING:

        async def create(self, *args, **kwargs) -> MODEL: ...

        def filter(self, *args: Q, **kwargs: Any) -> "Self": ...

        def exclude(self, *args: Q, **kwargs: Any) -> "Self": ...

        def order_by(self, *orderings: str) -> "Self": ...

        def offset(self, offset: int) -> "Self": ...

        def limit(self, limit: int) -> "Self": ...
