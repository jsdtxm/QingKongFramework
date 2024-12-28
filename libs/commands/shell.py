import code
import asyncio

from common.settings import settings
from libs.initialize.apps import init_apps
from libs.initialize.db import async_init_db, get_tortoise_config


def shell():
    loop = asyncio.get_event_loop()

    init_apps(settings.INSTALLED_APPS)
    loop.run_until_complete(async_init_db(get_tortoise_config(settings.DATABASES)))

    code.interact(local=locals())
