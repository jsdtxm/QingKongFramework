"""
All In One Server
"""

from contextlib import asynccontextmanager

from fastapi import APIRouter

from common.settings import settings
from fastapp.fastapi import FastAPI
from fastapp.initialize.apps import init_apps
from fastapp.router import router_convert


# FIXME 会丢失app自己设置的lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    apps = init_apps(settings.INSTALLED_APPS)
    app_configs = {
        k: x
        for k, x in apps.app_configs.items()
        if x.has_module("urls") and x.name not in settings.NO_EXPORT_APPS
    }

    for app_name, internal_app in app_configs.items():
        url_module = internal_app.import_module("urls")
        if url_module and (urlpatterns := getattr(url_module, "urlpatterns", None)):
            api_router = APIRouter(prefix=f"/{internal_app.prefix}", tags=[app_name])
            for router in router_convert(urlpatterns):
                api_router.include_router(**router)
            app.include_router(api_router)

    yield


asgi_app = FastAPI(lifespan=lifespan, auto_load_urls=False)
