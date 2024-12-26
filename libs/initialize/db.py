import inspect
import re
from importlib import import_module
from typing import Any

import uvloop

from libs.apps import Apps
from libs.models.base import TortoiseModel
from libs.models.tortoise import Tortoise
from libs.utils.module_loading import module_has_submodule, package_try_import


def get_tortoise_config(databases: dict[str, dict[str, Any]]):
    """
    Convert django database config to tortoise orm config
    """

    apps: Apps = import_module("libs.apps").apps

    tortoise_config = {
        "connections": {},
        "apps": {},
    }

    connection_routers = []
    for app_config in apps.app_configs.values():
        if models := package_try_import(app_config.module, "models"):
            flag = False
            for member_name in dir(models):
                obj = getattr(models, member_name)
                if (
                    not member_name.startswith("__")
                    and inspect.isclass(obj)
                    and issubclass(obj, TortoiseModel)
                    and not getattr(getattr(obj, "Meta", None), "abstract", False)
                ):
                    flag = True
                    break

            if not flag:
                continue

            models_module_path = app_config.name + ".models"
            app_model_config = {
                "models": [models_module_path],
                "default_connection": app_config.default_connection,
            }
            if hasattr(models, "Router"):
                connection_routers.append(models_module_path + ".Router")

            tortoise_config["apps"][app_config.label] = app_model_config

    for alias, config in databases.items():
        if re.search(r"sqlite3?$", config["ENGINE"]):
            c = {
                "engine": "libs.db.backends.sqlite",
                "credentials": {
                    "file_path": str(config["NAME"]),
                    "journal_mode": "WAL",
                    "journal_size_limit": 16384,
                },
            }
        else:
            credentials = {
                k.lower(): v for k, v in config.items() if k not in {"ENGINE", "NAME"}
            }
            credentials["database"] = config["NAME"]
            c = {
                "engine": "libs.db.backends." + config["ENGINE"].rsplit(".", 1)[-1],
                "credentials": credentials,
            }

        tortoise_config["connections"][alias] = c

    tortoise_config["routers"] = connection_routers

    return tortoise_config


def init_models():
    """
    init_models
    """

    apps: Apps = import_module("libs.apps").apps

    for app_config in apps.app_configs.values():
        if module_has_submodule(app_config.module, "models"):
            Tortoise.init_models([f"{app_config.name}.models"], app_config.label)


async def async_init_db(config: dict):
    await Tortoise.init(config)


def init_db(config: dict):
    uvloop.run(async_init_db(config))
