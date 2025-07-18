import asyncio

from common.settings import settings
from fastapp.contrib.healthz.utils import check_db_and_cache
from fastapp.initialize.apps import init_apps
from fastapp.initialize.cache import init_cache
from fastapp.initialize.db import async_init_db, get_tortoise_config


def check():
    loop = asyncio.get_event_loop()

    init_apps(settings.INSTALLED_APPS)
    loop.run_until_complete(async_init_db(get_tortoise_config(settings.DATABASES)))
    
    loop.run_until_complete(init_cache())

    loop.run_until_complete(check_db_and_cache())
