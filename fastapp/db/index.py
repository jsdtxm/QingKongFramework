from pypika.terms import Term
from tortoise.indexes import Index


class ExpressionIndex(Index):
    def __init__(
        self,
        func: Term,
        name: str,
    ):
        self.fields = []
        self.name = name
        self.expressions = [func]
        self.extra = ""
