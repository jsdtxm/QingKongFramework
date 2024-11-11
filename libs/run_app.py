import uvicorn
from libs.fastapi import FastAPI
from libs.initialize.apps import init_apps
from libs.initialize.db import init_db, get_tortoise_config
from common.settings import settings

def serve_app(app_name: str, host: str="127.0.0.1", workers=1, reload=False):
    
    apps = init_apps(settings.INSTALLED_APPS)
    app_config = apps.app_configs[f'apps.{app_name}']

    init_db(get_tortoise_config(settings.DATABASES))

    app = FastAPI()
    app.include_router(app_config.import_module("views").router)

    uvicorn.run(app, host=host, port=app_config.port, log_level="info", workers=workers, reload=reload)