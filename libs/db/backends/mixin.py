from typing import List, Type

from tortoise.models import Model


class SchemaGeneratorMixin:
    def _get_models_to_create(self, models_to_create: "List[Type[Model]]") -> None:
        from libs.models.tortoise import Tortoise

        for app in Tortoise.apps.values():
            for model in app.values():
                if model._meta.external:
                    continue
                if model._meta.db == self.client:
                    model._check()
                    models_to_create.append(model)

