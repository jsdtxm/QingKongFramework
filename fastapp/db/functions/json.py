from pypika.terms import Function


class JsonUnquote(Function):
    def __init__(self, expr, alias=None):
        super(JsonUnquote, self).__init__("JSON_UNQUOTE", expr, alias=alias)
