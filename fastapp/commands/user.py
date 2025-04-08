import getpass

import click
import uvloop

from common.settings import settings
from fastapp.contrib.auth import get_user_model
from fastapp.initialize.apps import init_apps
from fastapp.initialize.db import async_init_db, get_tortoise_config
from fastapp.models.tortoise import Tortoise


async def _createsuperuser():
    if (
        "fastapp.contrib.contenttypes" not in settings.INSTALLED_APPS
        or "fastapp.contrib.auth" not in settings.INSTALLED_APPS
    ):
        click.echo("ERROR required contrib.auth and contrib.contenttypes")
        return

    init_apps(settings.INSTALLED_APPS)
    await async_init_db(get_tortoise_config(settings.DATABASES))

    User = get_user_model()

    username = input("Username: ")

    email = input("Email: ")

    password, repeat_password = 1, 2

    while password != repeat_password:
        password = getpass.getpass("Password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters long")
            continue
        repeat_password = getpass.getpass("Repeat Password: ")

    user = await User.objects.create_user(
        username=username, email=email, password=password, is_superuser=True
    )

    print(f"User {user.username} created successfully")

    await Tortoise.close_connections()


def createsuperuser():
    uvloop.run(_createsuperuser())
