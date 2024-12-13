import json

from fastapi.routing import APIRouter

from libs.exceptions import HTTPException
from libs.registry.states import get_etcd_connections

router = APIRouter()

@router.get("/")
async def root():
    return {"Hello": "Registry"}


@router.post("/services/register")
async def register_service(name: str, address: str, port: int):
    """Register a new service or update an existing one in etcd."""
    service_data = {"name": name, "address": address, "port": port, "status": "UP"}

    # Serialize the service data to JSON string
    service_json = json.dumps(service_data)

    # Set the service into etcd under its name as key
    await get_etcd_connections().put(f"/services/{name}", service_json)

    return {"message": f"Service {name} registered"}


@router.get("/services")
async def list_services():
    """List all registered services from etcd."""
    services = []
    # Get all keys under /services/ prefix
    for key, value in await get_etcd_connections().range("/services/", prefix= True):
        # Deserialize the service data from JSON string
        service_data = json.loads(value.decode("utf-8"))
        services.append(service_data)

    return services


@router.delete("/services/{name}")
async def unregister_service(name: str):
    """Unregister a service by its name from etcd."""
    # Try to delete the service entry
    deleted = await get_etcd_connections().delete_range(f"/services/{name}")

    if not deleted:
        raise HTTPException(status_code=404, detail="Service not found")

    return {"message": f"Service {name} unregistered"}


@router.get("/services/{name}")
async def get_service(name: str):
    """Get a specific service by its name from etcd."""
    # Get the service entry
    values = (await get_etcd_connections().range(f"/services/{name}")).kvs

    if values is None:
        raise HTTPException(status_code=404, detail="Service not found")

    print(values)
    # Deserialize the service data from JSON string
    service_data = json.loads(values.decode("utf-8"))

    return {}
