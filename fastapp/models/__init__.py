from pypika.functions import Cast
from tortoise.expressions import Q, Subquery
from tortoise.fields.base import OnDelete
from tortoise.functions import Count, Sum
from tortoise.indexes import Index

from .base import BaseModel, Manager, QuerySet
from .fields import *
from .model import BaseMeta, Model
from .utils import get_object_or_404


PROTECT = OnDelete.RESTRICT