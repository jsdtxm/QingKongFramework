from common.settings import settings
from fastapp.apps.config import AppConfig


class AuthAppConfig(AppConfig):
    label = f"{settings.INTERNAL_APP_PREFIX}_auth"
    prefix = "auth"
