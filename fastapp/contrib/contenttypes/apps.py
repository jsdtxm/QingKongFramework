from common.settings import settings
from fastapp.apps.config import AppConfig


class ContentTypesAppConfig(AppConfig):
    label = f"{settings.INTERNAL_APP_PREFIX}_contenttypes"
