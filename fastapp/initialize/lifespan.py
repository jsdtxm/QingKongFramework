import contextlib

from common.settings import settings
from fastapp.initialize.apps import init_apps
from fastapp.initialize.cache import init_cache
from fastapp.initialize.db import async_init_db, get_tortoise_config
from fastapp.models.tortoise import Tortoise


@contextlib.asynccontextmanager
async def fastapp_lifespan(close=True):
    init_apps(settings.INSTALLED_APPS)
    await init_cache()
    await async_init_db(get_tortoise_config(settings.DATABASES))

    try:
        yield
    finally:
        if close:
            await Tortoise.close_connections()
