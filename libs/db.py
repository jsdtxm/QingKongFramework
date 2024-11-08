from tortoise import Tortoise

from core.settings import settings
from libs.adapter import config_to_tortoise


async def init_db():
    await Tortoise.init(config_to_tortoise(settings))
