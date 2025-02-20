from datetime import datetime
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar

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
        float: "float",
        bool: "bool",
        bytes: "bytes",
    }.get(t, str(t))
