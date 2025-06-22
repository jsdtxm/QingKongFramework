from typing import Any, Optional

import numpy as np
from pgvector import Vector
from tortoise.fields.base import Field


class VectorField(Field[np.ndarray], np.ndarray):
    """
    Accurate vector field.
    """

    skip_to_python_if_native = True

    def __init__(self, verbose_name=None, db_column=None, dimensions=None, **kwargs):
        self.verbose_name = verbose_name
        self.dimensions = dimensions

        if db_column:
            kwargs["source_field"] = db_column

        super().__init__(**kwargs)

    def to_python_value(self, value: Any) -> Optional[np.ndarray]:
        if isinstance(value, list):
            return np.array(value, dtype=np.float32)
        return Vector._from_db(value)

    @property
    def SQL_TYPE(self) -> str:  # type: ignore
        if self.dimensions is None:
            return "vector"
        return "vector(%d)" % self.dimensions
