from libs.apps.config import AppConfig
from common.settings import settings


class RegistryConfig(AppConfig):
    port = settings.REGISTRY_SERVICE_PORT
