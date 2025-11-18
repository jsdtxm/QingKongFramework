import inspect
import os
import types
from typing import Optional, Tuple, Type

from fastapp.conf import settings
from fastapp.exceptions import ImproperlyConfigured
from fastapp.utils.fs import get_existed_ports, read_port_from_json, write_port_to_json
from fastapp.utils.lock import FileLock
from fastapp.utils.module_loading import (
    cached_import_module,
    import_string,
    module_has_submodule,
)
from fastapp.utils.ports import find_free_port

APPS_MODULE_NAME = "apps"
MODELS_MODULE_NAME = "models"


class AppConfigMeta(type):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        if "name" not in attrs:
            attrs["name"] = attrs["__module__"].rsplit(".", 1)[0]
        if "label" not in attrs:
            attrs["label"] = attrs["name"].rpartition(".")[2]
        if "prefix" not in attrs:
            attrs["prefix"] = attrs["label"].replace(".", "_")

        return super().__new__(mcs, name, bases, attrs)


class AppConfig(metaclass=AppConfigMeta):
    name: str
    label: str
    prefix: str
    port: Optional[int] = None

    default_connection: str = "default"

    module: types.ModuleType
    models_module: types.ModuleType

    def __init__(self, name, module) -> None:
        self.name = name
        self.module = module

        if settings.ENABLE_PORT_MAP_FILE:
            host = os.environ.get("FASTAPP_SERVER_HOST", "127.0.0.1")
            app_name = os.environ.get("FASTAPP_SERVER_APP")
            command = os.environ.get("FASTAPP_COMMAND", "unknown")

            if command != "runserver":
                exists_config = read_port_from_json(name, lock=False)
                if exists_config and (p := exists_config.get("port")):
                    self.port = p
                elif self.has_module("urls") and name not in settings.NO_EXPORT_APPS:
                    raise Exception(f"App {name} port not found in service_ports.json")

                return

            if (
                app_name is None
                or self.name == app_name
                or self.name == f"apps.{app_name}"
            ):
                with FileLock(
                    name=f"{settings.PROJECT_NAME or settings.BASE_DIR.name}_choice_port.lock",
                    timeout=60,
                ):
                    if self.port:
                        write_port_to_json(name, self.port, address=host, lock=False)
                    elif self.has_module("urls"):
                        if name not in settings.NO_EXPORT_APPS:
                            exists_config = read_port_from_json(name, lock=False)
                            if exists_config and (p := exists_config.get("port")):
                                self.port = p
                            else:
                                self.port = find_free_port(
                                    exclude_ports=get_existed_ports()
                                )
                                write_port_to_json(
                                    name, self.port, address=host, lock=False
                                )

                            if exists_config and exists_config.get("address") != host:
                                write_port_to_json(
                                    name, self.port, address=host, lock=False
                                )

    def __str__(self):
        return f"<QingKongFramework.AppConfig {self.name}>"

    def __repr__(self):
        return self.__str__()

    @classmethod
    def create(cls, entry):
        """
        Factory that creates an app config from an entry in INSTALLED_APPS.
        """
        # create() eventually returns app_config_class(app_name, app_module).
        app_config_class = None
        app_name = None
        app_module = None

        # If import_module succeeds, entry points to the app module.
        try:
            app_module = cached_import_module(entry)
        except Exception:
            pass
        else:
            # If app_module has an apps submodule that defines a single
            # AppConfig subclass, use it automatically.
            # To prevent this, an AppConfig subclass can declare a class
            # variable default = False.
            # If the apps module defines more than one AppConfig subclass,
            # the default one can declare default = True.
            if module_has_submodule(app_module, APPS_MODULE_NAME):
                mod_path = "%s.%s" % (entry, APPS_MODULE_NAME)
                mod = cached_import_module(mod_path)
                # Check if there's exactly one AppConfig candidate,
                # excluding those that explicitly define default = False.
                app_configs = [
                    (name, candidate)
                    for name, candidate in inspect.getmembers(mod, inspect.isclass)
                    if (
                        issubclass(candidate, cls)
                        and candidate is not cls
                        and getattr(candidate, "default", True)
                    )
                ]
                if len(app_configs) == 1:
                    app_config_class = app_configs[0][1]
                else:
                    # Check if there's exactly one AppConfig subclass,
                    # among those that explicitly define default = True.
                    app_configs = [
                        (name, candidate)
                        for name, candidate in app_configs
                        if getattr(candidate, "default", False)
                    ]
                    if len(app_configs) > 1:
                        candidates = [repr(name) for name, _ in app_configs]
                        raise RuntimeError(
                            "%r declares more than one default AppConfig: "
                            "%s." % (mod_path, ", ".join(candidates))
                        )
                    elif len(app_configs) == 1:
                        app_config_class = app_configs[0][1]

            # Use the default app config class if we didn't find anything.
            if app_config_class is None:
                app_config_class = AppConfigMeta(
                    entry.rsplit(".", 1)[-1].capitalize() + "AppConfig",
                    (AppConfig,),
                    {"name": entry},
                )
                app_name = entry

        # If import_string succeeds, entry is an app config class.
        if app_config_class is None:
            try:
                app_config_class = import_string(entry)
            except ImportError as e:
                raise ImproperlyConfigured(
                    "Could not import '%s'. %s: %s." % (entry, e.__class__.__name__, e)
                ) from None
            except Exception as e:
                raise e

        # Check for obvious errors. (This check prevents duck typing, but
        # it could be removed if it became a problem in practice.)
        if not issubclass(app_config_class, AppConfig):
            raise ImproperlyConfigured("'%s' isn't a subclass of AppConfig." % entry)

        # Obtain app name here rather than in AppClass.__init__ to keep
        # all error checking for entries in INSTALLED_APPS in one place.
        if app_name is None:
            try:
                app_name = app_config_class.name
            except AttributeError:
                raise ImproperlyConfigured("'%s' must supply a name attribute." % entry)

        # Ensure app_name points to a valid module.
        try:
            app_module = cached_import_module(app_name)
        except ImportError:
            raise ImproperlyConfigured(
                "Cannot import '%s'. Check that '%s.%s.name' is correct."
                % (
                    app_name,
                    app_config_class.__module__,
                    app_config_class.__qualname__,
                )
            )

        # Entry is a path to an app config class.
        return app_config_class(app_name, app_module)

    def import_module(self, name: str):
        if module_has_submodule(self.module, name):
            module_name = "%s.%s" % (self.name, name)
            return cached_import_module(module_name)

    def has_module(self, name: str):
        return module_has_submodule(self.module, name)
