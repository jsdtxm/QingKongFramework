import inspect
import multiprocessing
import os
import signal
import socket
import sys
from collections import Counter
from pathlib import Path

import uvicorn
import uvicorn._subprocess

from common.settings import settings
from fastapp.initialize.apps import init_apps
from fastapp.logging import get_log_config_template
from fastapp.patchs.uvicorn.subprocess import subprocess_started
from fastapp.patchs.uvicorn.watchfilesreload import WatchFilesReload_init

try:
    import uvloop
except ImportError:
    uvloop = None

if uvloop is not None:
    uvloop.install()
    if settings.UVLOOP_WARNING:
        print("[uvloop installed]")


def serve_app(app_name: str, host: str = "127.0.0.1", workers=1, reload=False):
    os.environ["FASTAPP_SERVER_HOST"] = (
        host if host not in ["0.0.0.0", "::"] else socket.gethostname()
    )
    os.environ["FASTAPP_SERVER_APP"] = app_name
    os.environ["FASTAPP_COMMAND"] = "runserver"

    apps = init_apps(settings.INSTALLED_APPS)

    try:
        app_config = apps.app_configs[app_name]
    except KeyError:
        app_name = f"apps.{app_name}"
        app_config = apps.app_configs[app_name]

    # patch
    uvicorn.supervisors.watchfilesreload.WatchFilesReload.__init__ = (
        WatchFilesReload_init
    )

    log_config = get_log_config_template()
    for formatter in log_config["formatters"].values():
        formatter["app_label"] = app_config.label

    uvicorn.run(
        f"{app_name}.asgi:app",
        host=host,
        port=app_config.port,
        log_level="info",
        workers=workers,
        reload=reload,
        reload_dirs=[
            Path(inspect.getfile(inspect.getmodule(app_config))).parent,  # app dir
            Path(inspect.getfile(inspect.currentframe())).parent.parent,  # fastapp dir
            Path(inspect.getfile(inspect.getmodule(settings))).parent,  # common dir
        ]
        if reload
        else None,
        log_config=log_config,
    )


processes: list[multiprocessing.Process] = []


def signal_handler(sig, frame):
    print("Received Ctrl+C, terminating processes...", flush=True)
    for process in processes:
        if process.is_alive():
            process.terminate()
    sys.exit(0)


def _serve_app(config):
    return serve_app(*config)


def serve_apps(host: str = "127.0.0.1", workers=1, reload=False, exclude=[]):
    os.environ["FASTAPP_SERVER_HOST"] = (
        host if host not in ["0.0.0.0", "::"] else socket.gethostname()
    )
    os.environ["FASTAPP_COMMAND"] = "runserver"

    apps = init_apps(settings.INSTALLED_APPS)

    app_configs = [
        x
        for x in apps.app_configs.values()
        if x.name.split(".")[-1] not in exclude
        and x.has_module("urls")
        and x.name not in settings.NO_EXPORT_APPS
    ]

    # patch
    uvicorn._subprocess.subprocess_started = subprocess_started

    port_counter = Counter([app_config.port for app_config in app_configs])
    for _, count in port_counter.items():
        if count > 1:
            raise Exception("App port duplicate")

    app_params = list(
        map(
            lambda x: (x.name, host, workers, reload),
            app_configs,
        )
    )

    global processes

    # Create and start each process manually
    for param in app_params:
        p = multiprocessing.Process(
            target=_serve_app, args=(param,), daemon=False, name=param[0]
        )
        p.daemon = False  # Set daemon to False
        p.start()
        processes.append(p)

    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)

    # Wait for all processes to complete
    for process in processes:
        process.join()


def serve_app_aio(host: str = "127.0.0.1", port: int = 8080, workers=1, reload=False):
    uvicorn.run(
        "fastapp.serve.aio:asgi_app",
        host=host,
        port=port,
        log_level="info",
        workers=workers,
        reload=reload,
        reload_dirs=[] if reload else None,
        log_config=get_log_config_template(),
    )
