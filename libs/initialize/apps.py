from libs import apps

def init_apps(installed_apps):
    if apps.apps is None:
        apps.apps = apps.Apps(installed_apps)
    return apps.apps