from pypika.terms import Function
from typing import Any


class Abs(Function):
    def __init__(self, string_expression, alias=None):
        super(Abs, self).__init__("ABS", string_expression, alias=alias)


class Diff(Function):
    """Diff"""

    def __init__(self, field, value, alias=None):
        self.field = field
        self.value = value
        self.alias = alias

        self.args: list = []
        self.schema = None

    def get_function_sql(self, **kwargs: Any) -> str:
        return f'ABS({self.field} - {self.value})'
