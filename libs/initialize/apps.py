from typing import Sequence

from libs import apps


def init_apps(installed_apps: Sequence[str]):
    if len(installed_apps) != 0 and len(apps.apps.installed_apps) == 0:
        apps.apps.populate(installed_apps)
    
    return apps.apps
