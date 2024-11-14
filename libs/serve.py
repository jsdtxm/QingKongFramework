import multiprocessing
import multiprocessing.pool
import signal
import sys

import uvicorn

from common.settings import settings
from libs.initialize.apps import init_apps
from libs.initialize.db import get_tortoise_config, init_db


def serve_app(app_name: str, host: str = "127.0.0.1", workers=1, reload=False):
    apps = init_apps(settings.INSTALLED_APPS)
    app_config = apps.app_configs[f"apps.{app_name}"]

    init_db(get_tortoise_config(settings.DATABASES))

    uvicorn.run(
        f"apps.{app_name}.asgi:app",
        host=host,
        port=app_config.port,
        log_level="info",
        workers=workers,
        reload=reload,
    )


processes : list[multiprocessing.Process] = []


def signal_handler(sig, frame):
    print("Received Ctrl+C, terminating processes...", flush=True)
    for process in processes:
        if process.is_alive():
            process.terminate()
    sys.exit(0)

def _serve_app(config):
    return serve_app(*config)

def serve_apps(host: str = "127.0.0.1", workers=1, reload=False):
    apps = init_apps(settings.INSTALLED_APPS)
    app_params = list(
        map(
            lambda x: (x.label, host, workers, reload),
            filter(lambda x: x.name.startswith("apps."), apps.app_configs.values())
        )
    )

    global processes

    # Create and start each process manually
    for param in app_params:
        p = multiprocessing.Process(target=_serve_app, args=(param,))
        p.daemon = False  # Set daemon to False
        p.start()
        processes.append(p)

    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Wait for all processes to complete
    for process in processes:
        process.join()