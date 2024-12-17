import click

from common.settings import settings
from libs.initialize.apps import init_apps
from libs.initialize.db import init_models
from libs.misc import model_stub
from libs.misc.ascii_art import print_logo
from libs.utils.module_loading import package_try_import


def about():
    print_logo()


@click.option("--mode", default="lite", type=click.STRING)
def stubgen(mode="lite"):
    apps = init_apps(settings.INSTALLED_APPS)
    init_models()
    for app_config in apps.app_configs.values():
        if models := package_try_import(app_config.module, "models"):
            model_stub.generate(models.__name__, mode)
