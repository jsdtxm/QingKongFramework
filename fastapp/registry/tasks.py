import asyncio
import json

import aiohttp

from fastapp.registry.states import get_etcd_connections


async def check_service_health():
    """Asynchronously check the health of all registered services."""
    async with aiohttp.ClientSession() as session:
        for key, value in get_etcd_connections().get_prefix("/services/"):
            service_data = json.loads(value.decode("utf-8"))
            service_name = service_data["name"]
            service_address = service_data["address"]
            service_port = service_data["port"]

            try:
                # Try to reach the /healthz endpoint of the service
                async with session.get(
                    f"http://{service_address}:{service_port}/healthz", timeout=5
                ) as response:
                    if response.status == 200:
                        print(f"Service {service_name} is healthy.")
                    else:
                        print(
                            f"Service {service_name} returned an unexpected status code: {response.status}"
                        )
                        await update_service_status(service_name, "DOWN")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"Failed to reach service {service_name}: {e}")
                await update_service_status(service_name, "DOWN")


async def update_service_status(name: str, status: str):
    """Update the status of a service in etcd asynchronously."""
    key = f"/services/{name}"
    value, _ = get_etcd_connections().get(key)

    if value is None:
        return

    service_data = json.loads(value.decode("utf-8"))
    service_data["status"] = status
    get_etcd_connections().put(key, json.dumps(service_data))


async def periodic_check(interval: int):
    """Periodically check the health of services."""
    while True:
        await check_service_health()
        await asyncio.sleep(interval)
