from common.settings import settings
from libs.initialize.apps import init_apps
from libs.misc import model_stub
from libs.misc.ascii_art import print_logo
from libs.utils.module_loading import package_try_import


def about():
    print_logo()


def stubgen():
    apps = init_apps(settings.INSTALLED_APPS)
    for app_config in apps.app_configs.values():
        if models := package_try_import(app_config.module, "models"):
            model_stub.generate(models.__name__)
