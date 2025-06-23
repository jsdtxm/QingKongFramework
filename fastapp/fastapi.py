import inspect
from asyncio import create_task
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Callable, Optional, Sequence

from fastapi import BackgroundTasks as BackgroundTasks  # type: ignore
from fastapi import FastAPI as RawFastAPI
from fastapi import WebSocket as WebSocket  # type: ignore
from fastapi.applications import AppType
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi_pagination import add_pagination
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.types import Lifespan

import fastapp.patchs.fastapi.encoders as _
import fastapp.patchs.starlette.requests as _
from common.settings import settings
from fastapp.cache import connections
from fastapp.exception_handlers import get_default_exception_handlers
from fastapp.initialize.apps import init_apps
from fastapp.initialize.cache import init_cache
from fastapp.initialize.db import async_init_db, get_tortoise_config, init_models
from fastapp.middleware.trustedhost import TrustedHostMiddleware
from fastapp.models.tortoise import Tortoise
from fastapp.responses import JsonResponse
from fastapp.router import router_convert
from fastapp.utils.module_loading import import_string
from fastapp.utils.typing import copy_method_signature


@asynccontextmanager
async def default_lifespan(app: RawFastAPI):
    yield


def lifespan_wrapper(lifespan: Callable[[RawFastAPI], _AsyncGeneratorContextManager]):
    @asynccontextmanager
    async def wrapper(
        app: RawFastAPI,
    ):
        if p := settings.RATE_LIMITER_CLASS:
            import_string(p).init()

        if p := settings.XCAPTCHA_LIMITER_CLASS:
            await import_string(p).init()

        async with lifespan(app):
            yield

        await Tortoise.close_connections()

        for conn in connections.values():
            await conn.close()

    return wrapper


async def load_url_module(self, apps, package):
    url_module = apps.app_configs[package].import_module("urls")
    if url_module and (urlpatterns := getattr(url_module, "urlpatterns", None)):
        for router in router_convert(urlpatterns):
            self.include_router(**router)


class FastAPI(RawFastAPI):
    @copy_method_signature(RawFastAPI.__init__)
    def __init__(
        self,
        lifespan: Optional[Lifespan[AppType]] = None,
        include_healthz: bool = True,
        redirect_slashes=True,
        default_response_class=JsonResponse,
        auto_load_urls=True,
        middleware: Optional[list[Middleware]]=None,
        **kwargs,
    ):
        apps = init_apps(settings.INSTALLED_APPS)

        init_models()
        create_task(async_init_db(get_tortoise_config(settings.DATABASES)))
        create_task(init_cache())

        package = inspect.stack()[1].frame.f_locals.get("__package__")

        middleware: list[Middleware] = middleware or []
        for m in settings.MIDDLEWARE:
            middleware_class = import_string(m)
            middleware_kwargs = {}
            if middleware_class is TrustedHostMiddleware:
                middleware_kwargs = {"allowed_hosts": settings.ALLOWED_HOSTS}

            middleware.append(Middleware(middleware_class, **middleware_kwargs))

        super().__init__(
            lifespan=lifespan_wrapper(lifespan or default_lifespan),
            middleware=middleware,
            redirect_slashes=redirect_slashes,
            default_response_class=default_response_class,
            docs_url=None,
            **({"exception_handlers": get_default_exception_handlers()} | kwargs),
        )

        if include_healthz:
            self.include_router(import_string("fastapp.contrib.healthz.views.router"))

        if auto_load_urls:
            create_task(load_url_module(self, apps, package))

        # static assets
        async def custom_swagger_ui_html(req: Request) -> HTMLResponse:
            root_path = req.scope.get("root_path", "").rstrip("/")
            openapi_url = root_path + self.openapi_url
            oauth2_redirect_url = self.swagger_ui_oauth2_redirect_url
            if oauth2_redirect_url:
                oauth2_redirect_url = root_path + oauth2_redirect_url

            return get_swagger_ui_html(
                openapi_url=openapi_url,
                title=f"{self.title} - Swagger UI",
                oauth2_redirect_url=oauth2_redirect_url,
                init_oauth=self.swagger_ui_init_oauth,
                swagger_ui_parameters=self.swagger_ui_parameters,
                swagger_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.9.0/swagger-ui-bundle.js",
                swagger_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.9.0/swagger-ui.css",
                swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
            )

        self.add_route("/docs", custom_swagger_ui_html, include_in_schema=False)

        add_pagination(self)
