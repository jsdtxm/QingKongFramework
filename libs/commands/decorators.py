import functools

from common.settings import settings
from libs.initialize.apps import init_apps
from libs.initialize.db import async_init_db, get_tortoise_config
from libs.models.tortoise import Tortoise


def async_init_qingkong(func):
    @functools.wraps(func)  # 使用wraps以保留原始函数的元信息
    async def wrapper(*args, **kwargs):
        init_apps(settings.INSTALLED_APPS)
        await async_init_db(get_tortoise_config(settings.DATABASES))

        result = await func(*args, **kwargs)

        await Tortoise.close_connections()

        return result

    return wrapper
