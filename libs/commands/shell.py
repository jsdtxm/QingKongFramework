import asyncio
import code

from common.settings import settings
from libs.initialize.apps import init_apps
from libs.initialize.cache import init_cache
from libs.initialize.db import async_init_db, get_tortoise_config
from libs.models.tortoise import Tortoise


def shell():
    loop = asyncio.get_event_loop()

    init_apps(settings.INSTALLED_APPS)
    loop.run_until_complete(async_init_db(get_tortoise_config(settings.DATABASES)))

    init_cache()

    code.interact(local=locals())

    loop.run_until_complete(Tortoise.close_connections())
