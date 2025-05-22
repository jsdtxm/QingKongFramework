import operator
from typing import Dict

from pypika.terms import Criterion, Term
from tortoise.backends.mysql import executor
from tortoise.backends.mysql.executor import MySQLExecutor as RawMySQLExecutor
from tortoise.contrib.mysql.json_functions import (
    JSONExtract,
    _serialize_value,
    operator_keywords,
)
from tortoise.filters import (
    contains,
    ends_with,
    insensitive_contains,
    insensitive_ends_with,
    insensitive_exact,
    insensitive_starts_with,
    is_in,
    json_contained_by,
    json_contains,
    json_filter,
    posix_regex,
    search,
    starts_with,
)


def mysql_json_filter(field: Term, value: Dict) -> Criterion:
    if len(value) > 1:
        criterions = [
            mysql_json_filter(
                field,
                dict([x]),
            )
            for x in value.items()
        ]
        wheres = criterions[0]
        for c in criterions[1:]:
            wheres &= c
        return wheres

    ((key, filter_value),) = value.items()

    key_parts = [
        int(item)
        if item.isdigit()
        else str(item).replace("_\\_", "__")  # HACK add replace("_\\_", "__")
        for item in key.split("__")
    ]

    # HACK add is_in
    if len(key_parts) == 2 and key_parts[1] == "in":
        key_parts = key_parts[:-1]
        return is_in(JSONExtract(field, key_parts), filter_value)

    filter_value = _serialize_value(filter_value)

    operator_ = operator.eq
    if key_parts[-1] in operator_keywords:
        operator_ = operator_keywords[str(key_parts.pop(-1))]  # type: ignore

    return operator_(JSONExtract(field, key_parts), filter_value)


class MySQLExecutor(RawMySQLExecutor):
    FILTER_FUNC_OVERRIDE = {
        contains: executor.mysql_contains,
        starts_with: executor.mysql_starts_with,
        ends_with: executor.mysql_ends_with,
        insensitive_exact: executor.mysql_insensitive_exact,
        insensitive_contains: executor.mysql_insensitive_contains,
        insensitive_starts_with: executor.mysql_insensitive_starts_with,
        insensitive_ends_with: executor.mysql_insensitive_ends_with,
        search: executor.mysql_search,
        json_contains: executor.mysql_json_contains,
        json_contained_by: executor.mysql_json_contained_by,
        json_filter: mysql_json_filter,
        posix_regex: executor.mysql_posix_regex,
    }
