from itertools import chain

import click
import uvloop

from common.settings import settings
from libs.db.utils import generate_schemas
from libs.initialize.apps import init_apps
from libs.initialize.db import async_init_db, get_tortoise_config
from libs.models.tortoise import Tortoise
from libs.tools.reverse_generation import table_to_django_model

INTERNAL_CONTENTTYPES_APP_LABEL = "libs.contrib.contenttypes"
INTERNAL_AUTH_APP_LABEL = "libs.contrib.auth"
INTERNAL_GUARDIAN_APP_LABEL = "libs.contrib.guardian"


async def async_migrate(safe, guided, apps):
    auth_app_enabled = INTERNAL_AUTH_APP_LABEL in settings.INSTALLED_APPS
    guardian_app_enabled = INTERNAL_GUARDIAN_APP_LABEL in settings.INSTALLED_APPS
    content_type_app_enabled = (
        INTERNAL_CONTENTTYPES_APP_LABEL in settings.INSTALLED_APPS
    )

    if auth_app_enabled and not content_type_app_enabled:
        click.echo(
            f"ERROR {INTERNAL_AUTH_APP_LABEL} required {INTERNAL_CONTENTTYPES_APP_LABEL}"
        )
        return

    if guardian_app_enabled and not auth_app_enabled:
        click.echo(
            f"ERROR {INTERNAL_GUARDIAN_APP_LABEL} required {INTERNAL_AUTH_APP_LABEL}"
        )
        return

    init_apps(settings.INSTALLED_APPS)
    await async_init_db(get_tortoise_config(settings.DATABASES))
    await generate_schemas(Tortoise, safe=safe, guided=guided, apps=apps)

    if len(apps) > 0:
        await Tortoise.close_connections()

        return

    if content_type_app_enabled:
        from libs.contrib.contenttypes.models import ContentType

    if auth_app_enabled:
        from libs.contrib.auth.models import DefaultPerms, Permission

    # TODO object permission anonymous user

    if content_type_app_enabled:
        for x in chain.from_iterable(
            sub_dict.values() for sub_dict in Tortoise.apps.values()
        ):
            content_type, _ = await ContentType.get_or_create(
                app_label=x._meta.app_config.label, model=x.__name__
            )

            if auth_app_enabled:
                await Permission.bulk_create(
                    [
                        Permission(content_type=content_type, perm=p)
                        for p in DefaultPerms
                    ],
                    ignore_conflicts=True,
                )

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
