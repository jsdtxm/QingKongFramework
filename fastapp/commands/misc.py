from typing import Literal

import click

from common.settings import settings
from fastapp.initialize.apps import init_apps
from fastapp.initialize.db import init_models
from fastapp.misc import model_stub
from fastapp.misc.ascii_art import print_logo
from fastapp.misc.complete_type import complete, complete_choices
from fastapp.utils.module_loading import package_try_import


def about():
    print_logo()


@click.option("--mode", default="mini", type=click.STRING)
@click.option("--apps", multiple=True)
def stubgen(mode: Literal["lite", "full", "mini"] = "mini", apps=None):
    """
    stubgen
    """
    # TODO 有bug，比如alert模型的外键会瞎设置
    installed_apps = init_apps(settings.INSTALLED_APPS)
    init_models()

    app_configs = [
        x
        for x in installed_apps.app_configs.values()
        if not x.name.startswith("fastapp.contrib")
    ]

    for app_config in app_configs:
        if apps and app_config.label not in apps:
            continue
        if not isinstance(
            models := package_try_import(app_config.module, "models"), Exception
        ):
            if not models:
                continue
            model_stub.generate(models.__name__, mode)
            complete(models.__name__)
            complete_choices(models.__name__)

        else:
            raise models
