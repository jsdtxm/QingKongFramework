from common.settings import settings
from fastapp.apps.config import AppConfig


class KeyAuthAppConfig(AppConfig):
    label = f"{settings.INTERNAL_APP_PREFIX}_key_auth"
    prefix = "key_auth"
