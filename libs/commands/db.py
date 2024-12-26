import click
import uvloop

from common.settings import settings
from libs.db.utils import generate_schemas
from libs.initialize.apps import init_apps
from libs.initialize.db import async_init_db, get_tortoise_config
from libs.models.tortoise import Tortoise


async def async_migrate(safe, guided):
    if "libs.contrib.contenttypes" not in settings.INSTALLED_APPS:
        if "libs.contrib.auth" in settings.INSTALLED_APPS:
            click.echo("ERROR contrib.auth required contrib.contenttypes")
            return

    init_apps(settings.INSTALLED_APPS)
    await async_init_db(get_tortoise_config(settings.DATABASES))
    await generate_schemas(Tortoise, safe=safe, guided=guided)
    await Tortoise.close_connections()


@click.option("--safe", default=True)
@click.option("--guided", default=True)
def migrate(safe=True, guided=True):
    uvloop.run(async_migrate(safe, guided))
