from urllib.parse import urlparse

from etcd3 import AioClient

from common.settings import settings

etcd_connections = {}


async def init_etcd(alias="default"):
    parsed_url = urlparse(settings.ETCD_URL)
    client = AioClient(
        host=parsed_url.hostname,
        port=parsed_url.port,
        username=parsed_url.username,
        password=parsed_url.password,
    )
    await client.auth()
    etcd_connections[alias] = client


def get_etcd_connections(alias="default") -> AioClient:
    return etcd_connections[alias]
