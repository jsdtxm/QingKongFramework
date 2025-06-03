import asyncio
import inspect
import pkgutil
from importlib import import_module

import click

from fastapp.commands.decorators import async_init_fastapp


@async_init_fastapp
async def async_run_tests(apps: list[str]):
    from fastapp.apps import Apps

    installed_apps: Apps = import_module("fastapp.apps").apps
    for app_label, app_config in installed_apps.app_configs.items():
        if apps and app_label not in apps:
            continue

        if not app_config.has_module("tests"):
            continue

        print(f"Running tests for {app_label}")
        app_tests = app_config.import_module("tests")

        for _, modname, _ in pkgutil.walk_packages(
            path=app_tests.__path__, prefix=app_tests.__name__ + "."
        ):
            module = import_module(modname)

            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and (
                    name.startswith("test_") or name.startswith("perf_")
                ):
                    print(f"Running {name}")
                    if asyncio.iscoroutinefunction(obj):
                        await obj()
                    else:
                        obj()


@click.option("--apps", multiple=True)
def run_tests(apps=None):
    if apps is None:
        apps = []

    asyncio.run(async_run_tests(apps))
