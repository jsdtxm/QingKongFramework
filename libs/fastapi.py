import inspect
from asyncio import create_task
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Callable, Optional, Sequence

from fastapi import BackgroundTasks as BackgroundTasks  # type: ignore
from fastapi import FastAPI as RawFastAPI
from fastapi import WebSocket as WebSocket  # type: ignore
from fastapi.applications import AppType
from fastapi_pagination import add_pagination
from starlette.middleware import Middleware
from starlette.types import Lifespan

from common.settings import settings
from libs.cache import connections
from libs.exception_handlers import add_tortoise_exception_handler
from libs.initialize.apps import init_apps
from libs.initialize.cache import init_cache
from libs.initialize.db import async_init_db, get_tortoise_config, init_models
from libs.middleware.trustedhost import TrustedHostMiddleware
from libs.models.tortoise import Tortoise
from libs.responses import JsonResponse
from libs.router import router_convert
from libs.utils.module_loading import import_string
from libs.utils.typing import copy_method_signature

import libs.patchs.fastapi.encoders as _


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
        redirect_slashes=True,
        middleware: Sequence[Middleware] = [],
        default_response_class=JsonResponse,
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
            redirect_slashes=redirect_slashes,
            default_response_class=default_response_class,
            **kwargs,
        )

        if include_healthz:
            self.include_router(import_string("libs.contrib.healthz.views.router"))

        url_module = apps.app_configs[package].import_module("urls")
        if url_module and (urlpatterns := getattr(url_module, "urlpatterns", None)):
            for router in router_convert(urlpatterns):
                self.include_router(**router)

        add_pagination(self)

        add_tortoise_exception_handler(self)
