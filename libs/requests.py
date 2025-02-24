from fastapi.requests import Request as Request  # noqa
import typing
from typing import TYPE_CHECKING, Optional, Any
from libs.datastructures import FileFormData, UploadFile, StringFormData
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.datastructures import QueryParams

if TYPE_CHECKING:
    from libs.contrib.auth.typing import UserProtocol


class Empty:
    pass


class DjangoStyleRequest:
    """keep no additional data"""

    post_data: Any = None
    file_data: Any = None

    def __init__(self, request: Request, user: Optional["UserProtocol"] = None):
        self.request = request
        self.user = user

        self._data = Empty

    @property
    def GET(self):
        return QueryParamsWrap(self.request.query_params)

    @property
    async def POST(self) -> StringFormData:
        if self.post_data is None:
            self.post_data = {
                k: v
                for k, v in (await self.form()).items()
                if not isinstance(v, StarletteUploadFile)
            }

        return StringFormData(self.post_data)

    @property
    async def FILES(self) -> FileFormData:
        if self.file_data is None:
            self.file_data = {
                k: v
                for k, v in (await self.form()).items()
                if isinstance(v, StarletteUploadFile)
            }
            for v in self.file_data.values():
                v.__class__ = UploadFile

        return FileFormData(self.file_data)

    async def json(self):
        return await self.request.json()
    
    @property
    async def data(self):
        return await self.request.json()

    async def body(self):
        return await self.request.body()
    
    @property
    def headers(self):
        return self.request.headers
    
    @property
    def client(self):
        return self.request.client

    @property
    def method(self):
        return self.request.method

    @property
    def form(self):
        return self.request.form


class QueryParamsWrap:
    def __init__(self, query_params: QueryParams):
        self.inner = query_params

    def get(self, key: typing.Any):
        return self.inner.get(key)

    def getlist(self, key: typing.Any):
        return self.inner.getlist(key)

    def keys(self):
        return self.inner.keys()

    def values(self):
        return self.inner.values()

    def to_dict(self):
        res = {}
        for k in self.inner.keys():
            v = self.inner.getlist(k)
            if len(v) == 1:
                res[k] = v[0]
            else:
                res[k] = v

        return res

    def items(self):
        return self.inner.items()

    def multi_items(self):
        return self.inner.multi_items()
