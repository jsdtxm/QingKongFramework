from . import fields
from .base import BaseModel, BaseMeta


class Model(BaseModel):
    id = fields.BigIntegerField(primary_key=True)

    class Meta(BaseMeta):
        abstract = True
