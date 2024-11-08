from tortoise import Tortoise
from libs.db import init_db
import uvloop

async def async_migrate():
    await init_db()
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()
    print("COMPLETE")

def migrate():
    uvloop.run(async_migrate())