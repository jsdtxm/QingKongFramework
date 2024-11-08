from core.settings import Settings
import re


def config_to_tortoise(db_config: Settings):
    """
    Convert django database config to tortoise orm config
    """
    tortoise_config = {
        "connections": {},
        'apps': {
            'main': {
                'models': ['apps.main.models'],
                'default_connection': 'default',
            }
        },
    }
    for alias, config in db_config.DATABASES.items():
        if re.search(r'sqlite3?$', config["ENGINE"]):
            c = {
                "engine": "tortoise.backends.sqlite",
                "credentials": {
                    "file_path": str(config["NAME"]),
                    'journal_mode': 'WAL', 'journal_size_limit': 16384, 
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
