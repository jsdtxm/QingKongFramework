import functools

from common.settings import settings
from fastapp.initialize.apps import init_apps
from fastapp.initialize.cache import init_cache
from fastapp.initialize.db import async_init_db, get_tortoise_config
from fastapp.models.tortoise import Tortoise


def async_init_fastapp(func):
    @functools.wraps(func)  # 使用wraps以保留原始函数的元信息
    async def wrapper(*args, **kwargs):
        init_apps(settings.INSTALLED_APPS)
        await init_cache()
        await async_init_db(get_tortoise_config(settings.DATABASES))

        try:
            return await func(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            await Tortoise.close_connections()

    return wrapper
