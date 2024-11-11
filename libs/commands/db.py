from tortoise import Tortoise
from libs.initialize.apps import init_apps

from libs.initialize.db import async_init_db, get_tortoise_config
import uvloop
from common.settings import settings

async def async_migrate():
    init_apps(settings.INSTALLED_APPS)
    await async_init_db(get_tortoise_config(settings.DATABASES))
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()

def migrate():
    uvloop.run(async_migrate())
