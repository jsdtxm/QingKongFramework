import inspect
from asyncio import create_task
from contextlib import asynccontextmanager
from typing import Optional, Type

from fastapi import FastAPI as RawFastAPI
from fastapi.applications import AppType
from fastapi_pagination import add_pagination
from starlette.types import Lifespan

from common.settings import settings
from libs.apps.config import AppConfig
from libs.initialize.apps import init_apps
from libs.initialize.db import async_init_db, get_tortoise_config
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
        **kwargs,
    ):
        apps = init_apps(settings.INSTALLED_APPS)
        create_task(async_init_db(get_tortoise_config(settings.DATABASES)))

        name = name or inspect.stack()[1].filename.rsplit("/", 2)[-2]

        super().__init__(lifespan=lifespan or default_lifespan, **kwargs)

        self.include_router(
            apps.app_configs[f"apps.{name}"].import_module("views").router
        )
        add_pagination(self)
