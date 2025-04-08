from pathlib import Path
from typing import Any, List, Optional, Tuple

from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class BaseSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(env_prefix="QK_")

    PROJECT_NAME: Optional[str] = None

    BASE_DIR: Path
    SECRET_KEY: str = "longlivethegreatunityofthepeople"

    ALLOWED_HOSTS: List[str] = ["127.0.0.1", "localhost"]

    ADD_CORS_HEADERS: bool = False

    INSTALLED_APPS: List[str] = []

    NO_EXPORT_APPS: List[str] = []

    DATABASES: dict[str, dict[str, Any]]
    CACHES: dict[str, dict[str, Any]] = {}

    AUTH_USER_MODEL: str | None = None

    EXTRA_PROXY: List[Tuple[str, str]] = []

    RATE_LIMITER_CLASS: str = "fastapp.contrib.limiter.RedisRateLimiter"

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
