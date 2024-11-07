from tortoise.models import Model as TortoiseModel, ModelMeta
from typing import Any

class DjangoModelManager:
    asd: str = 1
    def __init__(self, model: TortoiseModel):
        self.model = model

    def create(self, *args, **kwargs):
        return self.model.create(*args, **kwargs)
    
    def filter(self, *args, **kwargs):
        return self.model.filter(*args, **kwargs)


class DjangoModelMeta(ModelMeta):
    objects: DjangoModelManager

    def __getattribute__(cls, name):
        if name == "objects":
            return DjangoModelManager(cls)
        return super().__getattribute__(name)


class Model(TortoiseModel, metaclass=DjangoModelMeta):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
