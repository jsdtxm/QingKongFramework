from libs import models


class ContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField("python model class name", max_length=100)

    class Meta:
        verbose_name = "content type"
        verbose_name_plural = "content types"
        db_table = "qingkong_content_type"
        unique_together = [["app_label", "model"]]

    def __str__(self):
        return f"{self.app_label}.{self.model}"
