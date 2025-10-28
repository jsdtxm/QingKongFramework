from typing import Any

from pypika.terms import Function as PypikaFunction


class Function(PypikaFunction):
    """
    support as_{dialect}
    ```
    def as_postgresql(self, **kwargs):
        return super().as_sql(compiler, connection, function="STRPOS", **extra_context)
    ```

    """

    def __init__(self, name, *args, alias=None):
        super(Function, self).__init__(name, *args, alias=alias)

    def as_sql(self, name, args, dialect, **kwargs):
        """new method, like django"""

        # pylint: disable=E1111
        special_params_sql = self.get_special_params_sql(dialect=dialect, **kwargs)

        return "{name}({args}{special})".format(
            name=name,
            args=",".join(
                self.get_arg_sql(arg, dialect=dialect, **kwargs) for arg in args
            ),
            special=(" " + special_params_sql) if special_params_sql else "",
        )

    def get_function_sql(self, **kwargs: Any) -> str:
        dialect = kwargs.pop("dialect", None)
        if dialect and (func := getattr(self, f"as_{dialect.value}", None)):
            return func(dialect=dialect, **kwargs)
        return self.as_sql(self.name, self.args, dialect=dialect, **kwargs)
