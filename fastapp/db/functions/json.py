from pypika.terms import Function


class JsonExtract(Function):
    def __init__(self, field, expr, alias=None):
        super(JsonExtract, self).__init__("JSON_EXTRACT", field, expr, alias=alias)


class JsonUnquote(Function):
    def __init__(self, expr, alias=None):
        super(JsonUnquote, self).__init__("JSON_UNQUOTE", expr, alias=alias)
