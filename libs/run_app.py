import uvicorn
from libs.fastapi import FastAPI
from libs.initialize.apps import init_apps
from libs.initialize.db import init_db, get_tortoise_config
from common.settings import settings

def serve_app(app: str, host: str="127.0.0.1", workers=1, reload=False):
    from importlib import import_module

    
    app_config = init_apps(settings.INSTALLED_APPS)
    print("INIT APP CONFIG COMPLETE")
    import_module("libs.contrib.auth.models")

    init_db(get_tortoise_config(settings.DATABASES))

    print(app_config.app_configs)
    
    return
    

    app = FastAPI()
    app.include_router(app_config.import_module("views").router)
    print("aaa")

    uvicorn.run(app, host=host, port=app_config.port, log_level="info", workers=workers, reload=reload)