from pypika.terms import Function

class Right(Function):
    def __init__(self, string_expression, length, alias=None):
        super(Right, self).__init__("RIGHT", string_expression, length, alias=alias)


class Instr(Function):
    # TODO postgresql 没有这个函数，需要使用STRPOS代替
    def __init__(self, string_expression, substring, alias=None):
        super(Instr, self).__init__("INSTR", string_expression, substring, alias=alias)
