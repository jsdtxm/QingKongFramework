from pypika.terms import Function

class Right(Function):
    def __init__(self, string_expression, length, alias=None):
        super(Right, self).__init__("RIGHT", string_expression, length, alias=alias)

