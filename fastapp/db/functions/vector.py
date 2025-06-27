from typing import Any

import numpy as np
from pypika.terms import Function


class CosineSimilarity(Function):
    """CosineSimilarity"""

    def __init__(self, field, vector: np.ndarray, alias=None):
        self.field = field
        self.vector = vector
        self.alias = alias

        self.args: list = []
        self.schema = None

    def get_function_sql(self, **kwargs: Any) -> str:
        return f"(\"{self.field}\" <=> '{self.vector.tolist()}'::vector)"
