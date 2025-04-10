from typing import Any, Optional
from uuid import UUID

from tortoise.fields import data as tortoise_data_fields

try:
    from asyncpg.pgproto.pgproto import UUID as AsyncpgUUID
except Exception:
    AsyncpgUUID = None


# Integer
class SmallIntegerField(tortoise_data_fields.SmallIntField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class IntegerField(tortoise_data_fields.IntField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class PositiveIntegerField(tortoise_data_fields.IntField):
    SQL_TYPE = "INT UNSIGNED"

    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)

    @property
    def constraints(self) -> dict:
        return {
            "ge": 0,
            "le": 4294967295,
        }

    class _db_postgres:
        SQL_TYPE = "BIGINT"
        GENERATED_SQL = "BIGSERIAL NOT NULL PRIMARY KEY"


class PositiveSmallIntegerField(tortoise_data_fields.SmallIntField):
    SQL_TYPE = "SMALLINT UNSIGNED"

    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)

    @property
    def constraints(self) -> dict:
        return {
            "ge": 0,
            "le": 65535,
        }

    class _db_postgres:
        SQL_TYPE = "INT"
        GENERATED_SQL = "SERIAL NOT NULL PRIMARY KEY"


class BigIntegerField(tortoise_data_fields.BigIntField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class SmallAutoField(SmallIntegerField):
    def __init__(self, verbose_name=None, primary_key=True, **kwargs: Any) -> None:
        super().__init__(verbose_name, primary_key, **kwargs)


class AutoField(IntegerField):
    def __init__(self, verbose_name=None, primary_key=True, **kwargs: Any) -> None:
        super().__init__(verbose_name, primary_key, **kwargs)


class BigAutoField(BigIntegerField):
    def __init__(self, verbose_name=None, primary_key=True, **kwargs: Any) -> None:
        super().__init__(verbose_name, primary_key, **kwargs)


# Float
class FloatField(tortoise_data_fields.FloatField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class DecimalField(tortoise_data_fields.DecimalField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


# String
class CharField(tortoise_data_fields.CharField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class TextField(tortoise_data_fields.TextField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class EmailField(CharField):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("max_length", 254)
        super().__init__(**kwargs)


# Time
class TimeField(tortoise_data_fields.TimeField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class DateField(tortoise_data_fields.DateField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class DateTimeField(tortoise_data_fields.DatetimeField):
    def __init__(
        self,
        verbose_name=None,
        db_column=None,
        auto_now: bool = False,
        auto_now_add: bool = False,
        **kwargs: Any,
    ) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(auto_now, auto_now_add, **kwargs)


class TimeDeltaField(tortoise_data_fields.TimeDeltaField):
    # Django don't support this field
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


# Others
class BooleanField(tortoise_data_fields.BooleanField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class BinaryField(tortoise_data_fields.BinaryField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class JSONField(tortoise_data_fields.JSONField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)


class UUIDField(tortoise_data_fields.UUIDField):
    def __init__(self, verbose_name=None, db_column=None, **kwargs: Any) -> None:
        self.verbose_name = verbose_name

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)

    def to_python_value(self, value: Any) -> Optional[UUID]:
        if value is None or isinstance(value, UUID):
            if AsyncpgUUID is not None and isinstance(value, AsyncpgUUID):
                return UUID(value.hex)

            return value
        return UUID(value)
