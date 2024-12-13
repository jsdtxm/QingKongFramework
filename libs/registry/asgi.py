import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI as RawFastAPI

from libs.fastapi import FastAPI
from libs.registry.states import init_etcd, etcd_connections
from libs.registry.tasks import periodic_check


@asynccontextmanager
async def lifespan(app: RawFastAPI):
    await init_etcd()
    # asyncio.create_task(periodic_check(60))
    yield

    for conn in etcd_connections.values():
        conn.http.clear()


app = FastAPI(lifespan=lifespan)
