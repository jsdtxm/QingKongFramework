from pathlib import Path
from typing import Any, List

from libs.settings import BaseSettings


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    INSTALLED_APPS: List[str] = [
        "libs.contrib.auth",
        "apps.main",
        "apps.fake",
    ]

    DATABASES: dict[str, dict[str, Any]] = {
        "default": {
            "ENGINE": "tortoise.backends.sqlite",
            "NAME": BASE_DIR / "db.sqlite3",
        },
    }


settings = Settings()