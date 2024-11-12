import multiprocessing
import multiprocessing.pool
import signal
import sys

import uvicorn
from fastapi_pagination import add_pagination

from common.settings import settings
from libs.fastapi import FastAPI
from libs.initialize.apps import init_apps
from libs.initialize.db import get_tortoise_config, init_db


def serve_app(app_name: str, host: str = "127.0.0.1", workers=1, reload=False):
    # TODO You must pass the application as an import string to enable 'reload' or 'workers'.

    apps = init_apps(settings.INSTALLED_APPS)
    app_config = apps.app_configs[f"apps.{app_name}"]

    init_db(get_tortoise_config(settings.DATABASES))

    app = FastAPI()
    app.include_router(app_config.import_module("views").router)
    add_pagination(app)

    uvicorn.run(
        app,
        host=host,
        port=app_config.port,
        log_level="info",
        workers=workers,
        reload=reload,
    )


pool: multiprocessing.pool.Pool = None


def signal_handler(sig, frame):
    print("Received Ctrl+C, terminating processes...", flush=True)
    pool.terminate()
    sys.exit(0)


def _serve_app(config):
    return serve_app(*config)


def serve_apps(host: str = "127.0.0.1", workers=1, reload=False):
    apps = init_apps(settings.INSTALLED_APPS)
    app_params = list(
        map(
            lambda x: (x.label, host, workers, reload),
            filter(lambda x: x.name.startswith("apps."), apps.app_configs.values()),
        )
    )

    global pool

    pool = multiprocessing.Pool(processes=len(app_params))
    signal.signal(signal.SIGINT, signal_handler)

    pool.map(_serve_app, app_params)

    pool.close()
    pool.join()
