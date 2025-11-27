from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar
from uuid import UUID

SP = ParamSpec("SP")
TR = TypeVar("TR")
TS = TypeVar("TS")


def copy_method_signature(
    f: Callable[Concatenate[Any, SP], Any],
) -> Callable[[Callable[Concatenate[TS, ...], TR]], Callable[Concatenate[TS, SP], TR]]:
    return lambda _: _  # type: ignore[return-value]


TYPE_MAPPING = {
    int: "int",
    str: "str",
    datetime: "datetime.datetime",
    date: "datetime.date",
    float: "float",
    bool: "bool",
    bytes: "bytes",
    UUID: "uuid.UUID",
    Decimal: "decimal.Decimal",
}

try:
    from numpy import ndarray

    TYPE_MAPPING[ndarray] = "numpy.ndarray"
except ImportError:
    pass


def type_to_str(t):
    return TYPE_MAPPING.get(t, str(t))
