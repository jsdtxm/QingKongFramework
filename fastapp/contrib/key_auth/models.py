from fastapp import models


class APIKey(models.Model):
    """
    A model to store and manage API keys.
    """

    name = models.CharField(max_length=255, default="Default")

    app_key = models.CharField(max_length=64)
    app_secret = models.CharField(max_length=64, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.suffix}..."  # Mask the full key for security reasons

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
