from datetime import datetime
from typing import Optional


def partition_by_year(
    field: str = "timestamp",
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    sub_partition: Optional[dict] = None,
):
    """
    Partition by year.
    """

    min_year = min_year or datetime.now().year
    max_year = max_year or min_year + 10

    return {
        "type": "RANGE",
        "fields": [field],
        "expr": "YEAR()",
        "sub_partition": sub_partition,
        "partitions": [
            {
                "name": f"p_{y}",
                "expr": f"LESS THAN ({y + 1})",
            }
            for y in range(min_year, max_year)
        ]
        + [
            {
                "name": "p_future",
                "expr": "LESS THAN MAXVALUE",
            }
        ],
    }
