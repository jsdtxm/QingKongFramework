import asyncio

from fastapp.commands.decorators import async_init_fastapp


@async_init_fastapp
async def async_init_dynamic_rbac():
    from fastapp.contrib.dynamic_rbac.utils import initialize_dynamic_permissions

    await initialize_dynamic_permissions()


def init_dynamic_rbac():
    asyncio.run(async_init_dynamic_rbac())
