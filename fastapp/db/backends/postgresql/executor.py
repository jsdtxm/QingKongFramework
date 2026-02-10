from typing import Any, Dict, Optional, TYPE_CHECKING, Union

import numpy as np
from pypika import Query
from tortoise.backends.asyncpg.executor import (
    AsyncpgExecutor as TortoiseAsyncpgExecutor,
)
from tortoise.expressions import RawSQL

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
