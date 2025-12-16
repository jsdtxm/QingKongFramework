import operator
from typing import Dict

from tortoise.filters import (
    FilterInfoDict,
    bool_encoder,
    is_null,
    json_contained_by,
    json_contains,
    json_encoder,
    json_filter,
    not_equal,
    not_null,
)

from fastapp.db.filters import json_endswith


def get_json_filter(field_name: str, source_field: str) -> Dict[str, FilterInfoDict]:
    actual_field_name = field_name
    return {
        field_name: {
            "field": actual_field_name,
            "source_field": source_field,
            "operator": operator.eq,
        },
        f"{field_name}__not": {
            "field": actual_field_name,
            "source_field": source_field,
            "operator": not_equal,
        },
        f"{field_name}__isnull": {
            "field": actual_field_name,
            "source_field": source_field,
            "operator": is_null,
            "value_encoder": bool_encoder,
        },
        f"{field_name}__not_isnull": {
            "field": actual_field_name,
            "source_field": source_field,
            "operator": not_null,
            "value_encoder": bool_encoder,
        },
        f"{field_name}__contains": {
            "field": actual_field_name,
            "source_field": source_field,
            "operator": json_contains,
        },
        f"{field_name}__contained_by": {
            "field": actual_field_name,
            "source_field": source_field,
            "operator": json_contained_by,
        },
        f"{field_name}__filter": {
            "field": actual_field_name,
            "source_field": source_field,
            "operator": json_filter,
            "value_encoder": json_encoder,
        },
        f"{field_name}__endswith": {
            "field": actual_field_name,
            "source_field": source_field,
            "operator": json_endswith,
            "value_encoder": json_encoder,
        },
    }


from tortoise import filters

filters.get_json_filter = get_json_filter
