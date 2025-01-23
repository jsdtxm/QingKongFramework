import json
import os
import typing
from io import IOBase
from starlette.background import BackgroundTask
from starlette.responses import FileResponse as StarletteFileResponse  # noqa
from starlette.responses import HTMLResponse as HTMLResponse  # noqa
from starlette.responses import JSONResponse as StarletteJSONResponse  # noqa
from starlette.responses import PlainTextResponse as PlainTextResponse  # noqa
from starlette.responses import RedirectResponse as RedirectResponse  # noqa
from starlette.responses import Response as Response  # noqa
from starlette.responses import StreamingResponse as StreamingResponse  # noqa

from libs.utils.json import JSONEncoder


class JSONResponse(StarletteJSONResponse):
    def __init__(
        self,
        content: typing.Any = None,
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content: typing.Any) -> bytes:
        if content is None:
            return b""
        
        return json.dumps(
            content,
            cls=JSONEncoder,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


class JsonResponse(JSONResponse):
    pass


class ResponseHeaderOperatorsMixin:
    def __getitem__(self, key):
        return self.headers[key]

    def __setitem__(self, key, value):
        self.headers[key] = value


class HttpResponse(ResponseHeaderOperatorsMixin, Response):
    def __init__(
        self,
        content: typing.Any = None,
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
        content_type: str | None = None,
        background: BackgroundTask | None = None,
        charset: str = "urf-8",
    ) -> None:
        self.charset = charset

        super().__init__(content, status_code, headers, content_type, background)


class FileResponse(ResponseHeaderOperatorsMixin, StarletteFileResponse):
    def __init__(
        self,
        path: IOBase | str | os.PathLike[str],
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str = "application/octet-stream",
        background: BackgroundTask | None = None,
        filename: str | None = None,
        stat_result: os.stat_result | None = None,
        method: str | None = None,
        content_disposition_type: str = "attachment",
    ) -> None:
        if isinstance(path, IOBase):
            path.close()
            path = getattr(path, "name", None)

            if path is None:
                raise Exception("Not support this type")

        super().__init__(
            path,
            status_code,
            headers,
            media_type,
            background,
            filename,
            stat_result,
            method,
            content_disposition_type,
        )


class HttpResponseNotAllowed(HttpResponse):
    def __init__(self, permitted_methods, status_code: int = 405, **kwargs) -> None:
        super().__init__(
            None, status_code, headers={"Allow": ", ".join(permitted_methods)}, **kwargs
        )
