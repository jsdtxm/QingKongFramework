from pathlib import Path
from typing import Any, List, Optional, Tuple

from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class BaseSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(env_prefix="QK_")

    BASE_DIR: Path
    SECRET_KEY: str

    ALLOWED_HOSTS: List[str] = ["127.0.0.1", "localhost"]

    INSTALLED_APPS: List[str]

    DATABASES: dict[str, dict[str, Any]]
    CACHES: dict[str, dict[str, Any]]

    AUTH_USER_MODEL: str | None = None

    EXTRA_PROXY: List[Tuple[str, str]] = []

    XCAPTCHA_URL: Optional[str] = None
    XCAPTCHA_ENCRYPT_KEY: Optional[str] = None
    XCAPTCHA_API_KEY: Optional[str] = None

    XCAPTCHA_SERVICE_PORT: int = 28000
