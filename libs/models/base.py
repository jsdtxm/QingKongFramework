from typing import Any, Tuple, Type, Union

from tortoise.manager import Manager as TortoiseManager
from tortoise.models import Model as TortoiseModel
from tortoise.models import ModelMeta as TortoiseModelMeta
from tortoise.queryset import QuerySet

from libs import apps
from libs.apps.config import AppConfig


class Manager(TortoiseManager):
    _model: TortoiseModel

    def create(self, *args, **kwargs):
        return self._model.create(*args, **kwargs)


class ModelMeta(TortoiseModelMeta):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        module_name: str = attrs["__module__"]
        if module_name.endswith(".models"):
            app_config = apps.apps.app_configs[module_name.rsplit(".", 1)[0]]
            attrs["app"] = app_config

            meta_class = attrs.get("Meta", type("Meta", (), {}))
            table = getattr(meta_class, "table", None)
            if table is None:
                meta_class.table = f"{app_config.label}_{name.lower()}"
                attrs["Meta"] = meta_class

        return super().__new__(mcs, name, bases, attrs)


class BaseModel(TortoiseModel, metaclass=ModelMeta):
    objects: Union[Manager, QuerySet] = Manager()

    app: AppConfig

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    class Meta:
        manager = Manager()
