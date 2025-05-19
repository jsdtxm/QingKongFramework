from typing import TYPE_CHECKING, Type

from pypika.terms import Term
from tortoise.indexes import Index

if TYPE_CHECKING:
    from tortoise import Model
    from tortoise.backends.base.schema_generator import BaseSchemaGenerator


class ExpressionIndex(Index):
    def __init__(
        self,
        func: Term,
        name: str,
    ):
        self.fields = []
        self.name = name
        self.expressions = (func,)
        self.extra = ""

    def get_sql(
        self, schema_generator: "BaseSchemaGenerator", model: "Type[Model]", safe: bool
    ):
        if self.fields:
            fields = ", ".join(schema_generator.quote(f) for f in self.fields)
        else:
            blank_quote = schema_generator.quote("")
            quote_char = blank_quote[0] if blank_quote else ""

            expressions = [
                f"({expression.get_sql(quote_char=quote_char)})"
                for expression in self.expressions
            ]
            fields = ", ".join(expressions)

        return self.INDEX_CREATE_TEMPLATE.format(
            exists="IF NOT EXISTS " if safe else "",
            index_name=schema_generator.quote(self.index_name(schema_generator, model)),
            index_type=f" {self.INDEX_TYPE} ",
            table_name=schema_generator.quote(model._meta.db_table),
            fields=fields,
            extra=self.extra,
        )
