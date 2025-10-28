from tortoise.expressions import F, Q, RawSQL, Subquery
from tortoise.fields.base import OnDelete
from tortoise.functions import Count, Max, Min, Sum, Trim
from tortoise.indexes import Index

from fastapp.db.index import ExpressionIndex

from .base import BaseModel
from .fields import *
from .functions import (
    Abs,
    Cast,
    Diff,
    Instr,
    JsonExtract,
    JsonUnquote,
    Right,
    StrIndex,
    Substr,
)
from .manager import Manager
from .model import BaseMeta, Model
from .queryset import QuerySet
from .utils import get_object_or_404

PROTECT = OnDelete.RESTRICT
