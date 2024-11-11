from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI as RawFastAPI
from fastapi.applications import AppType
from starlette.types import Lifespan

from libs.utils.typing import copy_method_signature


@asynccontextmanager
async def default_lifespan(app: RawFastAPI):
    yield


class FastAPI(RawFastAPI):
    @copy_method_signature(RawFastAPI.__init__)
    def __init__(self, lifespan: Optional[Lifespan[AppType]] = None, **kwargs):
        return super().__init__(lifespan=lifespan or default_lifespan, **kwargs)
