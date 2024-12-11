import inspect
from asyncio import create_task
from contextlib import asynccontextmanager
from importlib import import_module
from typing import Optional, Sequence, Type

from fastapi import FastAPI as RawFastAPI
from fastapi.applications import AppType
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi_pagination import add_pagination
from starlette.middleware import Middleware
from starlette.types import Lifespan

from common.settings import settings
from libs.apps.config import AppConfig
from libs.initialize.apps import init_apps
from libs.initialize.cache import init_cache
from libs.initialize.db import async_init_db, get_tortoise_config, init_models
from libs.router import router_convert
from libs.utils.typing import copy_method_signature


@asynccontextmanager
async def default_lifespan(app: RawFastAPI):
    yield


class FastAPI(RawFastAPI):
    @copy_method_signature(RawFastAPI.__init__)
    def __init__(
        self,
        name: Type[AppConfig] = None,
        lifespan: Optional[Lifespan[AppType]] = None,
        include_healthz: bool = True,
        middleware: Sequence[Middleware] = [],
        **kwargs,
    ):
        apps = init_apps(settings.INSTALLED_APPS)

        init_models()
        create_task(async_init_db(get_tortoise_config(settings.DATABASES)))

        init_cache()

        name = name or inspect.stack()[1].filename.rsplit("/", 2)[-2]

        if not any((m.cls is TrustedHostMiddleware for m in middleware)):
            middleware.append(
                Middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
            )

        super().__init__(
            lifespan=lifespan or default_lifespan, middleware=middleware, **kwargs
        )

        if include_healthz:
            self.include_router(import_module("libs.contrib.healthz.views").router)

        for router in router_convert(
            apps.app_configs[f"apps.{name}"].import_module("urls").urlpatterns
        ):
            self.include_router(**router)

        add_pagination(self)
