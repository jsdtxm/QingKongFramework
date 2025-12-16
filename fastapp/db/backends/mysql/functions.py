from typing import Any

from pypika.terms import Criterion, Term, ValueWrapper
from pypika.terms import Function as PypikaFunction


# Json Endswith
class JSONEndswith(PypikaFunction):  # type: ignore
    def __init__(self, column_name: Term, target: Term):
        super(JSONEndswith, self).__init__("JSON_ENDSWITH", column_name, target)

    def get_function_sql(self, **kwargs: Any) -> str:
        column_name, target = [self.get_arg_sql(arg, **kwargs) for arg in self.args]

        return "{column_name} -> '$[last]' = {target}".format(
            column_name=column_name,
            target=target,
        )


def mysql_json_endswith(field: Term, value: str) -> Criterion:
    return JSONEndswith(field, ValueWrapper(value))
