import re
from importlib.util import find_spec

from core.settings import Settings


def config_to_tortoise(db_config: Settings):
    """
    Convert django database config to tortoise orm config
    """

    tortoise_config = {
        "connections": {},
        "apps": {},
    }

    for app in Settings.INSTALLED_APPS:
        if "." not in app:
            app = f"apps.{app}"

        if not find_spec(app):
            raise Exception("app not found: %s", app)

        if find_spec(f"{app}.models"):
            tortoise_config["apps"][app] = {
                "models": [app + ".models"],
                "default_connection": "default",
            }

    for alias, config in db_config.DATABASES.items():
        if re.search(r"sqlite3?$", config["ENGINE"]):
            c = {
                "engine": "tortoise.backends.sqlite",
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
                "engine": "tortoise.backends." + config["ENGINE"].split(".")[-1],
                "credentials": credentials,
            }

        tortoise_config["connections"][alias] = c

    return tortoise_config
