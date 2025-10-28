from pypika.functions import Cast as PypikaCast
from tortoise.fields.base import Field


class FieldToSQLTypeWrapper:
    __slots__ = ("field",)

    def __init__(self, field: Field) -> None:
        self.field = field

    def get_sql(self, **kwargs) -> str:
        return self.field.SQL_TYPE


class Cast(PypikaCast):
    def __init__(self, term, as_type, alias=None) -> None:
        super(PypikaCast, self).__init__("CAST", term, alias=alias)
        self.as_type = (
            FieldToSQLTypeWrapper(as_type) if isinstance(as_type, Field) else as_type
        )
