from . import fields
from .base import BaseModel


class Model(BaseModel):
    id = fields.BigIntegerField(primary_key=True)

    class Meta:
        abstract = True
