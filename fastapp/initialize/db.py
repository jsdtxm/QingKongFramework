import asyncio
import inspect
import re
from importlib import import_module
from typing import Any

from fastapp.apps import Apps
from fastapp.conf import settings
from fastapp.models.base import TortoiseModel
from fastapp.models.tortoise import Tortoise
from fastapp.utils.module_loading import package_try_import

async_lock = asyncio.Lock()
is_init_db = False


def models_is_empty(models):
    for member_name in dir(models):
        obj = getattr(models, member_name)
        if (
            not member_name.startswith("__")
            and inspect.isclass(obj)
            and issubclass(obj, TortoiseModel)
            and not getattr(getattr(obj, "Meta", None), "abstract", False)
        ):
            return False

    return True


def get_tortoise_config(databases: dict[str, dict[str, Any]]):
    """
    Convert django database config to tortoise orm config
    """

    apps: Apps = import_module("fastapp.apps").apps

    tortoise_config = {
        "connections": {},
        "apps": {},
        "timezone": settings.TIME_ZONE,
    }

    connection_routers = []
    for app_config in apps.app_configs.values():
        if not isinstance(
            models := package_try_import(app_config.module, "models"), Exception
        ):
            if models_is_empty(models):
                continue

            models_module_path = app_config.name + ".models"
            app_model_config = {
                "models": [models_module_path],
                "default_connection": app_config.default_connection,
            }
            if hasattr(models, "Router"):
                connection_routers.append(models_module_path + ".Router")

            tortoise_config["apps"][app_config.label] = app_model_config

        else:
            raise models

    for alias, config in databases.items():
        if re.search(r"sqlite3?$", config["ENGINE"]):
            c = {
                "engine": "fastapp.db.backends.sqlite",
                "credentials": {
                    "file_path": str(config["NAME"]),
                    "journal_mode": "WAL",
                    "journal_size_limit": 16384,
                },
            }
        else:
            if "." in config["ENGINE"]:
                engine = config["ENGINE"]
            else:
                engine = "fastapp.db.backends." + config["ENGINE"].rsplit(".", 1)[-1]

            credentials = {
                k.lower(): v for k, v in config.items() if k not in {"ENGINE", "NAME"}
            }
            credentials["database"] = config["NAME"]
            c = {
                "engine": engine,
                "credentials": credentials,
            }

        tortoise_config["connections"][alias] = c

    tortoise_config["routers"] = connection_routers

    return tortoise_config


def _init_models():
    """
    init_models
    """

    apps: Apps = import_module("fastapp.apps").apps

    for app_config in apps.app_configs.values():
        if not isinstance(
            models := package_try_import(app_config.module, "models"), Exception
        ):
            if models_is_empty(models):
                continue
            Tortoise.init_models([f"{app_config.name}.models"], app_config.label)
        else:
            raise Exception(f"App {app_config.label} import error") from models


models_inited = False


def init_models():
    """
    init_models
    """
    global models_inited
    if models_inited:
        return
    _init_models()
    models_inited = True


async def async_init_db(config: dict):
    global is_init_db

    async with async_lock:
        if is_init_db:
            return
        await Tortoise.init(config)
        is_init_db = True


def init_db(config: dict):
    asyncio.run(async_init_db(config))
