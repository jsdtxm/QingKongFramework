from libs import models
from typing import Self


class ContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField("python model class name", max_length=100)

    class Meta:
        verbose_name = "content type"
        verbose_name_plural = "content types"
        db_table = "qingkong_content_type"
        unique_together = [["app_label", "model"]]

    @classmethod
    async def from_model(cls, model_cls: models.Model) -> Self:
        return await cls.objects.get(
            app_label=model_cls._meta.app_config.label, model=model_cls.__name__
        )

    def __str__(self):
        return f"{self.app_label}.{self.model}"
