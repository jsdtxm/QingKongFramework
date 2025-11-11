from typing import Sequence

from fastapp import apps


def init_apps(installed_apps: Sequence[str], override: bool = False):
    """Initialize apps"""
    if len(installed_apps) != 0 and (override or len(apps.apps.installed_apps) == 0):
        apps.apps.populate(installed_apps)

    return apps.apps
