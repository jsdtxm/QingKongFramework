from itertools import chain

import click
import uvloop

from common.settings import settings
from libs.db.utils import generate_schemas
from libs.initialize.apps import init_apps
from libs.initialize.db import async_init_db, get_tortoise_config
from libs.models.tortoise import Tortoise
from libs.tools.reverse_generation import table_to_django_model


async def async_migrate(safe, guided, apps):
    if "libs.contrib.contenttypes" not in settings.INSTALLED_APPS:
        if "libs.contrib.auth" in settings.INSTALLED_APPS:
            click.echo("ERROR contrib.auth required contrib.contenttypes")
            return

    init_apps(settings.INSTALLED_APPS)
    await async_init_db(get_tortoise_config(settings.DATABASES))
    await generate_schemas(Tortoise, safe=safe, guided=guided, apps=apps)

    if "libs.contrib.contenttypes" in settings.INSTALLED_APPS:
        from libs.contrib.contenttypes.models import ContentType

        await ContentType.get_or_create(
            app_label=ContentType.app.label, model=ContentType.__name__
        )

        for x in chain.from_iterable(
            sub_dict.values() for sub_dict in Tortoise.apps.values()
        ):
            if x is ContentType:
                continue

            await ContentType.get_or_create(app_label=x.app.label, model=x.__name__)

    await Tortoise.close_connections()


@click.option("--safe", default=True)
@click.option("--guided", default=True)
@click.option("--apps", multiple=True)
def migrate(safe=True, guided=True, apps=[]):
    uvloop.run(async_migrate(safe, guided, apps))


async def print_result(func, *args, **kwargs):
    print(await func(*args, **kwargs))


@click.argument("table")
@click.option("--connection", default="default")
@click.option("--db", default=None)
def reverse_generation(connection, db, table):
    db_config = settings.DATABASES[connection]

    uvloop.run(
        print_result(
            table_to_django_model,
            {
                "host": db_config["HOST"],
                "port": db_config["PORT"],
                "user": db_config["USER"],
                "password": db_config["PASSWORD"],
                "db": db or db_config["NAME"],
            },
            table,
        )
    )
