from typing import Any, Self

from pypika.dialects.mysql import MySQLLoadQueryBuilder, MySQLQueryBuilder
from pypika.queries import Query
from pypika.terms import ArithmeticExpression, Field, Function
from pypika.utils import builder


class ClickHouseQuery(Query):
    """
    Defines a query class for use with ClickHouse.
    """

    @classmethod
    def _builder(cls, **kwargs: Any) -> "ClickHouseQueryBuilder":
        return ClickHouseQueryBuilder(**kwargs)

    @classmethod
    def load(cls, fp: str) -> "ClickHouseLoadQueryBuilder":
        return ClickHouseLoadQueryBuilder().load(fp)


class ClickHouseLoadQueryBuilder(MySQLLoadQueryBuilder):
    QUERY_CLS = ClickHouseQuery


class ClickHouseQueryBuilder(MySQLQueryBuilder):
    def get_sql(self, **kwargs: Any) -> str:  # type:ignore[override]
        self._set_kwargs_defaults(kwargs)
        querystring = super().get_sql(**kwargs)
        if querystring:
            if self._update_table:
                if self._orderbys:
                    querystring += self._orderby_sql(**kwargs)
                if self._limit:
                    querystring += self._limit_sql()
        return querystring
    
    @builder
    def select(self, *terms: Any) -> "Self":  # type:ignore[return]
        for term in terms:
            if isinstance(term, Field):
                self._select_field(term)
            elif isinstance(term, str):
                self._select_field_str(term)
            elif isinstance(term, (Function, ArithmeticExpression)):
                self._select_other(term)  # type:ignore[arg-type]
            else:
                self._select_other(
                    self.wrap_constant(term, wrapper_cls=self._wrapper_cls)  # type:ignore[arg-type]
                )
