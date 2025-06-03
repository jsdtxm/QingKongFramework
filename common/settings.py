from pathlib import Path
from typing import Any, List

from fastapp.conf import BaseSettings


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    INSTALLED_APPS: List[str] = [
        "fastapp.contrib.auth",
        "apps.main",
        "apps.fake",
    ]

    DATABASES: dict[str, dict[str, Any]] = {
        "default": {
            "ENGINE": "tortoise.backends.sqlite",
            "NAME": BASE_DIR / "db.sqlite3",
        },
    }

    CACHES: dict[str, dict[str, Any]] = {
        "default": {
            "BACKEND": "RedisCache",
            "LOCATION": "redis://[USERNAME]:[PASSWORD]@[IP]:[PORT]/[DB]",
        },
        "disk": {
            "BACKEND": "fastapp.cache.DiskCacheBackend",
            "DIRECTORY": "./.cache",
        },
    }


settings = Settings()