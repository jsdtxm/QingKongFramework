import re
from importlib import import_module
from typing import Any

import uvloop
from tortoise import Tortoise

from libs.apps import Apps
from libs.utils.module_loading import module_has_submodule


def get_tortoise_config(databases: dict[str, dict[str, Any]]):
    """
    Convert django database config to tortoise orm config
    """

    apps: Apps = import_module("libs.apps").apps

    tortoise_config = {
        "connections": {},
        "apps": {},
    }

    for app_config in apps.app_configs.values():
        if module_has_submodule(app_config.module, "models"):
            tortoise_config["apps"][app_config.label] = {
                "models": [app_config.name + ".models"],
                "default_connection": "default",
            }

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
                "engine": "libs.db.backends." + config["ENGINE"].split(".")[-1],
                "credentials": credentials,
            }

        tortoise_config["connections"][alias] = c
    
    return tortoise_config


async def async_init_db(config: dict):
    await Tortoise.init(config)


def init_db(config: dict):
    uvloop.run(async_init_db(config))
