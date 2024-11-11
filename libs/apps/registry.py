from .config import AppConfig
from libs.exceptions import ImproperlyConfigured

class Apps:
    """
    A registry that stores the configuration of installed applications.

    It also keeps track of models, e.g. to provide reverse relations.
    """

    app_configs: dict[str, AppConfig] = {}


    def __init__(self, installed_apps=()):
        self.populate(installed_apps)

    def populate(self, installed_apps=None):
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

        # for app_config in self.app_configs.values():
        #     app_config.import_models()
