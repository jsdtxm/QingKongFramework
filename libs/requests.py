from fastapi.requests import Request as Request  # noqa
from typing import TYPE_CHECKING, Optional
from libs.datastructures import FileFormData, UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile


if TYPE_CHECKING:
    from libs.contrib.auth.typing import UserProtocol


class Empty:
    pass

class DjangoStyleRequest:
    """keep no additional data"""
    
    def __init__(self, request: Request, user: Optional["UserProtocol"]=None):
        self.request = request
        self.user = user

        self._data = Empty

    @property
    def GET(self):
        return self.request.query_params

    @property
    def POST(self):
        return self.form()
    
    @property
    async def FILES(self) -> FileFormData:
        form = {k: v for k, v in (await self.form()).items() if isinstance(v, StarletteUploadFile)}
        for v in form.values():
            v.__class__ = UploadFile

        return FileFormData(form)
    
    @property
    def method(self):
        return self.request.method
    
    @property
    def form(self):
        return self.request.form