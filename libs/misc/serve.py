import multiprocessing
import multiprocessing.pool
import signal
import sys
from collections import Counter
from copy import deepcopy

import uvicorn
import uvicorn._subprocess

from common.settings import settings
from libs.initialize.apps import init_apps
from libs.logging import log_config_template
from libs.patchs.uvicorn.subprocess import subprocess_started
from libs.patchs.uvicorn.watchfilesreload import WatchFilesReload_init


def serve_app(app_name: str, host: str = "127.0.0.1", workers=1, reload=False):
    apps = init_apps(settings.INSTALLED_APPS)
    app_config = apps.app_configs[f"apps.{app_name}"]

    # patch
    uvicorn.supervisors.watchfilesreload.WatchFilesReload.__init__ = (
        WatchFilesReload_init
    )

    log_config = deepcopy(log_config_template)
    for formatter in log_config["formatters"].values():
        formatter["app_label"] = app_config.label

    uvicorn.run(
        f"apps.{app_name}.asgi:app",
        host=host,
        port=app_config.port,
        log_level="info",
        workers=workers,
        reload=reload,
        reload_dirs=[f"/workspace/polypro_backend/apps/{app_name}"] if reload else None,
        log_config=log_config
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
    apps = init_apps(settings.INSTALLED_APPS)

    app_configs = [x for x in apps.app_configs.values() if x.name.split(".")[-1] not in exclude]

    # patch
    uvicorn._subprocess.subprocess_started = subprocess_started

    port_counter = Counter(
        [app_config.port for app_config in app_configs]
    )
    for _, count in port_counter.items():
        if count > 1:
            print("app port duplicate")

    app_params = list(
        map(
            lambda x: (x.label, host, workers, reload),
            filter(lambda x: x.name.startswith("apps."), app_configs),
        )
    )

    global processes

    # Create and start each process manually
    for param in app_params:
        p = multiprocessing.Process(target=_serve_app, args=(param,), daemon=False)
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
