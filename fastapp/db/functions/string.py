from fastapp.db.functions.base import Function
from pypika.terms import NullValue

class Right(Function):
    def __init__(self, string_expression, length, alias=None):
        super(Right, self).__init__("RIGHT", string_expression, length, alias=alias)


class Instr(Function):
    def __init__(self, string_expression, substring, alias=None):
        super(Instr, self).__init__("INSTR", string_expression, substring, alias=alias)

    def as_postgresql(self, **kwargs):
        return super().as_sql("STRPOS", self.args, **kwargs)

class Substr(Function):
    def __init__(self, string_expression, start, length=None, alias=None):
        super(Substr, self).__init__(
            "SUBSTR", string_expression, start, length, alias=alias
        )

    def get_function_sql(self, **kwargs) -> str:
        args = self.args[:2] if isinstance(self.args[2], NullValue) else self.args
        return self.as_sql(self.name, args, **kwargs)

StrIndex = Instr
