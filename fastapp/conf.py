from pathlib import Path
from typing import Any, List, Optional, Tuple, TYPE_CHECKING

from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict

if TYPE_CHECKING:
    from common.settings import Settings


class BaseSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(env_prefix="QK_")

    PROJECT_NAME: Optional[str] = None

    TIME_ZONE: str = "Asia/Shanghai"

    BASE_DIR: Path
    SECRET_KEY: str = "longlivethegreatunityofthepeople"

    ALLOWED_HOSTS: List[str] = ["127.0.0.1", "localhost"]

    ADD_CORS_HEADERS: bool = False

    INSTALLED_APPS: List[str] = []

    NO_EXPORT_APPS: List[str] = []

    DATABASES: dict[str, dict[str, Any]]
    CACHES: dict[str, dict[str, Any]] = {}

    EXTRA_PROXY: List[Tuple[str, str]] = []

    RATE_LIMITER_CLASS: str = "fastapp.contrib.limiter.cache.CacheRateLimiter"
    WEBSOCKET_RATE_LIMITER_CLASS: str = (
        "fastapp.contrib.limiter.cache.WebSocketCacheRateLimiter"
    )

    XCAPTCHA_URL: Optional[str] = None
    XCAPTCHA_ENCRYPT_KEY: Optional[str] = None
    XCAPTCHA_API_KEY: Optional[str] = None

    XCAPTCHA_LIMITER_CLASS: str = "fastapp.contrib.xcaptcha.XCaptchaLimiter"
    XCAPTCHA_SERVICE_PORT: int = 28000

    ETCD_URL: str = "etcd://root:wskj123456@etcd:2379"

    AUTH_USER_MODEL: str = "fastapp.contrib.auth.models.User"

    ACCESS_TOKEN_LIFETIME: int = 60 * 60
    REFRESH_TOKEN_LIFETIME: int = 60 * 60 * 24 * 7

    AUTH_PERMISSION_BACKEND: str = (
        "fastapp.contrib.auth.backends.permission.ModelPermissionBackend"
    )

    INTERNAL_APP_PREFIX: str = "qingkong"

    # EMAIL
    EMAIL_BACKEND: str = "fastapp.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST: str = "smtp.example.com"
    EMAIL_PORT: int = 465
    EMAIL_HOST_USER: str = ""
    EMAIL_HOST_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    EMAIL_USE_SSL: bool = False
    EMAIL_USE_TLS: bool = False
    EMAIL_TIMEOUT: Optional[int] = None
    EMAIL_SUBJECT_PREFIX: str = "[FastAPP]"
    EMAIL_SSL_CERTFILE: Optional[str] = None
    EMAIL_SSL_KEYFILE: Optional[str] = None
    EMAIL_USE_LOCALTIME: bool = False
    DEFAULT_FROM_EMAIL: str = "webmaster@localhost"
    SERVER_EMAIL: str = "root@localhost"

    ADMINS: List[str] = []
    DEFAULT_CHARSET: str = "utf-8"

    ENABLE_PORT_MAP_FILE: bool = True

    DEFAULT_PAGINATION_CLASS: Optional[str] = None


class LazySettings:
    """
    A class for lazily loading settings.

    This class provides a mechanism to load settings in a lazy manner.
    It stores an instance of `BaseSettings` and loads it only when necessary.
    It also allows accessing attributes of the settings object through itself.
    """

    settings: Optional[BaseSettings] = None

    def __init__(self) -> None:
        pass

    def load_settings(self) -> BaseSettings:
        """
        Load and return an instance of BaseSettings.

        If the settings have already been loaded, it returns the cached instance.
        Otherwise, it imports the settings from `common.conf` and caches the instance.

        Returns:
            BaseSettings: An instance of the BaseSettings class containing application settings.
        """
        if self.settings is None:
            from common.settings import (
                settings as project_settings,  # pylint: disable=import-outside-toplevel
            )

            self.settings = project_settings

        return self.settings

    def __getattr__(self, name: str) -> Any:
        return self.load_settings().__getattribute__(name)


settings: "Settings" = LazySettings()  # type: ignore
