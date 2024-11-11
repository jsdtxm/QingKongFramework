from typing import Any, Callable, Concatenate, ParamSpec, TypeVar

SP = ParamSpec("SP")
TR = TypeVar("TR")
TS = TypeVar("TS")


def copy_method_signature(
    f: Callable[Concatenate[Any, SP], Any],
) -> Callable[[Callable[Concatenate[TS, ...], TR]], Callable[Concatenate[TS, SP], TR]]:
    return lambda _: _  # type: ignore[return-value]
