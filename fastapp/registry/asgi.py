import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI as RawFastAPI

from fastapp.fastapi import FastAPI
from fastapp.registry.states import init_etcd, etcd_connections
from fastapp.registry.tasks import periodic_check


@asynccontextmanager
async def lifespan(app: RawFastAPI):
    await init_etcd()
    # asyncio.create_task(periodic_check(60))
    yield

    for conn in etcd_connections.values():
        conn.http.clear()


app = FastAPI(lifespan=lifespan)
