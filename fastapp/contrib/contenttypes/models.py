from typing import Self, Type

from common.settings import settings
from fastapp import models


class ContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField("python model class name", max_length=100)

    class Meta:
        verbose_name = "content type"
        verbose_name_plural = "content types"
        db_table = f"{settings.INTERNAL_APP_PREFIX}_content_type"
        unique_together = [["app_label", "model"]]

    @classmethod
    async def from_model(cls, model: models.Model | Type[models.Model]) -> Self:
        if isinstance(model, type):
            return await cls.objects.get(
                app_label=model._meta.app_config.label, model=model.__name__
            )

        return await cls.objects.get(
            app_label=model._meta.app_config.label, model=model.__class__.__name__
        )

    @property
    def model_class(self) -> Type[models.Model]:
        from fastapp.models.tortoise import Tortoise

        return Tortoise.apps.get(self.app_label, {})[self.model]

    def __str__(self):
        return f"{self.app_label}.{self.model}"
