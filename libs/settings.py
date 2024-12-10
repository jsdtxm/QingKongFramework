from pathlib import Path
from typing import Any, List

from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class BaseSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(env_prefix="QK_")

    BASE_DIR: Path
    INSTALLED_APPS: List[str]
    DATABASES: dict[str, dict[str, Any]]

    AUTH_USER_MODEL: str | None = None
