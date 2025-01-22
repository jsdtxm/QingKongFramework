from fastapi.requests import Request as Request  # noqa
from typing import TYPE_CHECKING, Optional, Any
from libs.datastructures import FileFormData, UploadFile, StringFormData
from starlette.datastructures import UploadFile as StarletteUploadFile


if TYPE_CHECKING:
    from libs.contrib.auth.typing import UserProtocol


class Empty:
    pass

class DjangoStyleRequest:
    """keep no additional data"""

    post_data: Any = None
    file_data: Any = None
    
    def __init__(self, request: Request, user: Optional["UserProtocol"]=None):
        self.request = request
        self.user = user

        self._data = Empty

    @property
    def GET(self):
        return self.request.query_params

    @property
    async def POST(self) -> StringFormData:
        if self.post_data is None:
            self.post_data = {k: v for k, v in (await self.form()).items() if not isinstance(v, StarletteUploadFile)}
        
        return StringFormData(self.post_data)
    
    @property
    async def FILES(self) -> FileFormData:
        if self.file_data is None:
            self.file_data = {k: v for k, v in (await self.form()).items() if isinstance(v, StarletteUploadFile)}
            for v in self.file_data.values():
                v.__class__ = UploadFile

        return FileFormData(self.file_data)
    
    @property
    async def data(self):
        return await self.request.json()
    
    @property
    def method(self):
        return self.request.method
    
    @property
    def form(self):
        return self.request.form