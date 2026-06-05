from typing import Any, Dict, Iterable, Optional, Tuple, TYPE_CHECKING, Union, cast

import numpy as np
from pypika import Query
from tortoise.backends.asyncpg.executor import (
    AsyncpgExecutor as TortoiseAsyncpgExecutor,
)
from tortoise.expressions import RawSQL
from tortoise.fields.relational import RelationalField

if TYPE_CHECKING:  # pragma: nocoverage
    from tortoise.models import Model


class AsyncpgExecutor(TortoiseAsyncpgExecutor):
    # HACK
    async def execute_select(
        self, query: Union[Query, RawSQL], custom_fields: Optional[list] = None
    ) -> list:
        _, raw_results = await self.db.execute_query(query.get_sql())
        instance_list = []
        for row in raw_results:
            if self.select_related_idx:
                _, current_idx, _, _, path = self.select_related_idx[0]
                row_items = list(dict(row).items())
                instance: "Model" = self.model._init_from_db(
                    **dict(row_items[:current_idx])
                )
                instances: Dict[Any, Any] = {path: instance}
                for model, index, *__, full_path in self.select_related_idx[1:]:
                    (*path, attr) = full_path
                    related_items = row_items[current_idx : current_idx + index]
                    if not any(
                        v is None if type(v) is np.ndarray else bool(v)
                        for _, v in related_items
                    ):
                        obj = None
                    else:
                        obj = model._init_from_db(
                            **{k.split(".")[1]: v for k, v in related_items}
                        )
                    target = instances.get(tuple(path))
                    if target is not None:
                        setattr(target, f"_{attr}", obj)
                    if obj is not None:
                        instances[(*path, attr)] = obj
                    current_idx += index
            else:
                instance = self.model._init_from_db(**row)
            if custom_fields:
                for field in custom_fields:
                    setattr(instance, field, row[field])
            instance_list.append(instance)
        await self._execute_prefetch_queries(instance_list)
        return instance_list

    # HACK: Fix prefetch when FK source_field differs from the default "{field}_id" pattern.
    # Tortoise hardcodes `relation_key_field = f"{field}_id"` in _prefetch_direct_relation,
    # which breaks when db_column/source_field is set to a non-standard name (e.g. "clientid").
    async def _prefetch_direct_relation(
        self,
        instance_list: "Iterable[Model]",
        field: str,
        related_query: Tuple[Optional[str], "Any"],
    ) -> "Iterable[Model]":
        to_attr, related_queryset = related_query
        related_objects_for_fetch: Dict[str, list] = {}
        model_to_field: Dict["type[Model]", str] = {}

        # Use the actual source_field from the FK definition instead of hardcoded "{field}_id"
        instance_list = list(instance_list)
        if not instance_list:
            return instance_list
        related_field = cast(
            RelationalField, instance_list[0].__class__._meta.fields_map[field]
        )
        relation_key_field = related_field.source_field or f"{field}_id"

        for instance in instance_list:
            if (value := getattr(instance, relation_key_field, None)) is not None:
                if (model_cls := instance.__class__) in model_to_field:
                    key = model_to_field[model_cls]
                else:
                    field_obj = cast(
                        RelationalField, instance._meta.fields_map[field]
                    )
                    model_to_field[model_cls] = key = field_obj.to_field
                    if key not in related_objects_for_fetch:
                        related_objects_for_fetch[key] = []
                if value not in (values := related_objects_for_fetch[key]):
                    values.append(value)
            else:
                setattr(instance, field, None)

        if related_objects_for_fetch:
            conditions: Dict[str, Any] = {}
            for k, v in related_objects_for_fetch.items():
                if len(v) == 1:
                    v = v[0]
                else:
                    k += "__in"
                conditions[k] = v
            related_object_list = await related_queryset.filter(**conditions)
            if len(model_to_field) > 1:
                related_object_map = {
                    getattr(obj, model_to_field[obj.__class__]): obj
                    for obj in related_object_list
                }
            else:
                related_object_map = {
                    getattr(obj, key): obj for obj in related_object_list
                }
            for instance in instance_list:
                obj = related_object_map.get(
                    getattr(instance, relation_key_field, None)
                )
                setattr(instance, field, obj)
                if to_attr:
                    setattr(instance, to_attr, obj)
        return instance_list
