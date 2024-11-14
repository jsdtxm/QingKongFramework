from . import fields
from .base import BaseModel, BaseMeta


class Model(BaseModel):
    # TODO 考虑下生成pyi文件，不然filter之类的都不能智能提示了
    id = fields.BigIntegerField(primary_key=True)

    class Meta(BaseMeta):
        abstract = True
