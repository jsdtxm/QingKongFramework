import operator
from typing import Any, Union

from pypika import Field as PypikaField
from pypika.terms import ArithmeticExpression
from tortoise.expressions import F
from tortoise.expressions import Function as TortoiseFunction

import fastapp.db.functions.json as json_func
import fastapp.db.functions.number as number_func
import fastapp.db.functions.string as string_func


class Function(TortoiseFunction):
    """
    base class for tortoise function
    """

    __slots__ = ("field", "field_object", "default_values", "arithmetics")

    arithmetics: list[tuple[Any, Any]]

    def __init__(
        self,
        field: Union[str, F, ArithmeticExpression, "Function"],
        *default_values: Any,
    ) -> None:
        super().__init__(field, *default_values)
        self.arithmetics = []

    def _get_function_field(
        self, field: Union[ArithmeticExpression, PypikaField, str], *default_values
    ):
        instance = self.database_func(field, *default_values)  # type: ignore
        if self.arithmetics:
            # TODO 处理算术表达式
            for op, other in self.arithmetics:
                instance = op(instance, other)
        return instance

    # TODO add more arithmetic operators
    def __add__(self, other):
        self.arithmetics.append((operator.add, other))
        return self

    def __sub__(self, other):
        self.arithmetics.append((operator.sub, other))
        return self


class Right(Function):
    """
    RIGHT

    :samp:`RIGHT("{FIELD_NAME}", {length})`
    """

    database_func = string_func.Right


class Instr(Function):
    """
    INSTR

    :samp:`INSTR("{FIELD_NAME}", {length})`
    """

    database_func = string_func.Instr


class Substr(Function):
    """
    SUBSTR

    :samp:`SUBSTR("{FIELD_NAME}", {start}, {length})`
    """

    database_func = string_func.Substr


StrIndex = Instr


class JsonUnquote(Function):
    """
    JSON_UNQUOTE
    """

    database_func = json_func.JsonUnquote


class JsonExtract(Function):
    """
    JSON_EXTRACT
    """

    database_func = json_func.JsonExtract


class Abs(Function):
    """
    ABS
    """

    database_func = number_func.Abs


class Diff(Function):
    """
    DIFF
    """

    database_func = number_func.Diff
