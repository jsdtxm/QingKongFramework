from uuid6 import uuid7

from fastapp import models
from fastapp.contrib.auth.utils import get_user_model

User = get_user_model()


class APIKey(models.Model):
    """
    A model to store and manage API keys.
    """

    uuid = models.UUIDField(max_length=32, default=lambda: uuid7().hex)
    name = models.CharField(max_length=255, default="Default")

    user = models.ForeignKey(User, on_delete=models.PROTECT)

    suffix = models.CharField(max_length=32, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return (
            f"{self.name} - {self.suffix}..."  # Mask the full key for security reasons
        )

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
