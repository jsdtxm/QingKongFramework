import inspect
from asyncio import create_task
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Callable, Optional, Sequence

from fastapi import FastAPI as RawFastAPI
from fastapi.applications import AppType
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi_pagination import add_pagination
from starlette.middleware import Middleware
from starlette.types import Lifespan
from tortoise import Tortoise

from common.settings import settings
from libs.cache import connections
from libs.initialize.apps import init_apps
from libs.initialize.cache import init_cache
from libs.initialize.db import async_init_db, get_tortoise_config, init_models
from libs.router import router_convert
from libs.utils.module_loading import import_string
from libs.utils.typing import copy_method_signature


@asynccontextmanager
async def default_lifespan(app: RawFastAPI):
    yield


def lifespan_wrapper(lifespan: Callable[[RawFastAPI], _AsyncGeneratorContextManager]):
    @asynccontextmanager
    async def wrapper(
        app: RawFastAPI,
    ):
        if p := settings.RATE_LIMITER_CLASS:
            await import_string(p).init()

        if p := settings.XCAPTCHA_LIMITER_CLASS:
            await import_string(p).init()

        async with lifespan(app):
            yield

        await Tortoise.close_connections()

        for conn in connections.values():
            await conn.close()

    return wrapper


class FastAPI(RawFastAPI):
    @copy_method_signature(RawFastAPI.__init__)
    def __init__(
        self,
        lifespan: Optional[Lifespan[AppType]] = None,
        include_healthz: bool = True,
        middleware: Sequence[Middleware] = [],
        **kwargs,
    ):
        apps = init_apps(settings.INSTALLED_APPS)

        init_models()
        create_task(async_init_db(get_tortoise_config(settings.DATABASES)))

        init_cache()

        package = inspect.stack()[1].frame.f_locals.get("__package__")

        if not any((m.cls is TrustedHostMiddleware for m in middleware)):
            middleware.append(
                Middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
            )

        super().__init__(
            lifespan=lifespan_wrapper(lifespan or default_lifespan),
            middleware=middleware,
            **kwargs,
        )

        if include_healthz:
            self.include_router(import_string("libs.contrib.healthz.views.router"))

        for router in router_convert(
            apps.app_configs[package].import_module("urls").urlpatterns
        ):
            self.include_router(**router)

        add_pagination(self)
