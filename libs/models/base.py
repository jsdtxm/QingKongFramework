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


class BaseMeta:
    manager = Manager()
    external: bool = False
    app: str = "none"


class ModelMetaClass(TortoiseModelMeta):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        module_name: str = attrs.get("__module__", None)
        if module_name and module_name.endswith(".models"):
            meta_class = attrs.get("Meta", type("Meta", (BaseMeta,), {}))
            abstract = getattr(meta_class, "abstract", False)

            if not abstract:
                app_config = apps.apps.app_configs[module_name.rsplit(".", 1)[0]]
                attrs["app"] = app_config
                meta_class.app = app_config.label

            table = getattr(meta_class, "table", None)
            if table is None:
                db_table = getattr(meta_class, "db_table", None)
                if db_table:
                    meta_class.table = db_table
                elif not abstract:
                    meta_class.table = f"{app_config.label}_{name.lower()}"

            attrs["Meta"] = meta_class

        return super().__new__(mcs, name, bases, attrs)


class BaseModel(TortoiseModel, metaclass=ModelMetaClass):
    objects: Union[Manager, QuerySet] = Manager()

    app: AppConfig

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    class Meta(BaseMeta):
        pass

    class PydanticMeta:
        include = ()
        exclude = ()
        max_recursion = 1
