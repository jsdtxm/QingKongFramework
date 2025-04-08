from datetime import datetime, date
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar
from uuid import UUID
from decimal import Decimal

SP = ParamSpec("SP")
TR = TypeVar("TR")
TS = TypeVar("TS")


def copy_method_signature(
    f: Callable[Concatenate[Any, SP], Any],
) -> Callable[[Callable[Concatenate[TS, ...], TR]], Callable[Concatenate[TS, SP], TR]]:
    return lambda _: _  # type: ignore[return-value]


def type_to_str(t):
    return {
        int: "int",
        str: "str",
        datetime: "datetime.datetime",
        date: "datetime.date",
        float: "float",
        bool: "bool",
        bytes: "bytes",
        UUID: "uuid.UUID",
        Decimal: "decimal.Decimal"
    }.get(t, str(t))
