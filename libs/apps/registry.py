from typing import Sequence

from libs.exceptions import ImproperlyConfigured

from .config import AppConfig


class Apps:
    """
    A registry that stores the configuration of installed applications.

    It also keeps track of models, e.g. to provide reverse relations.
    """

    app_configs: dict[str, AppConfig] = {}
    installed_apps: Sequence[str] = []

    def __init__(self, installed_apps: Sequence[str] = []):
        self.populate(installed_apps)

    def populate(self, installed_apps=None):
        self.installed_apps = installed_apps
        for entry in installed_apps:
            if isinstance(entry, AppConfig):
                app_config = entry
            else:
                app_config = AppConfig.create(entry)
            if app_config.name in self.app_configs:
                raise ImproperlyConfigured(
                    "Application labels aren't unique, "
                    "duplicates: %s" % app_config.name
                )

            self.app_configs[app_config.name] = app_config

    def get_app_config(self, app_name: str):
        if app_name in self.app_configs:
            return self.app_configs[app_name]
        else:
            for app_config in self.app_configs.values():
                if app_config.__module__.rsplit(".", 1)[0] == app_name:
                    return app_config

        raise ImproperlyConfigured("App with label %s could not be found" % app_name)
