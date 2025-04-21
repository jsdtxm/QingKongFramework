try:
    import orjson
except ImportError:
    orjson = None
    import json

import decimal
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
from starlette.responses import StreamingResponse as StarletteStreamingResponse  # noqa

from fastapp.utils.json import JSONEncoder, default_datetime_format, replace_nan


def orjson_default_decimal(obj):
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    raise TypeError


class JSONResponse(StarletteJSONResponse):
    # 到这边之前会被fastapi的serialize_response处理(fastapi.routing.serialize_response)
    # 还有可能被fastapi.encoders.jsonable_encoder处理
    def __init__(
        self,
        content: typing.Any = None,
        status_code: int = 200,
        status: typing.Optional[int] = None,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
        orjson_parse_datetime: bool = False,
        json_replace_nan: bool = False,
    ) -> None:
        self.orjson_parse_datetime = orjson_parse_datetime
        self.json_replace_nan = json_replace_nan

        super().__init__(
            content, status or status_code, headers, media_type, background
        )

    def render(self, content: typing.Any) -> bytes:
        if content is None:
            return b""

        if orjson:
            if self.orjson_parse_datetime:
                content = default_datetime_format(content)
            return orjson.dumps(content, default=orjson_default_decimal)

        if self.json_replace_nan:
            content = replace_nan(content)

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
        status: typing.Optional[int] = None,
        headers: typing.Mapping[str, str] | None = None,
        content_type: str | None = None,
        background: BackgroundTask | None = None,
        charset: str = "utf-8",
    ) -> None:
        self.charset = charset

        super().__init__(
            content, status or status_code, headers, content_type, background
        )


class FileResponse(ResponseHeaderOperatorsMixin, StarletteFileResponse):
    def __init__(
        self,
        path: IOBase | str | os.PathLike[str],
        status_code: int = 200,
        status: typing.Optional[int] = None,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str = "application/octet-stream",
        content_type: typing.Optional[str] = None,
        background: BackgroundTask | None = None,
        filename: str | None = None,
        stat_result: os.stat_result | None = None,
        method: str | None = None,
        content_disposition_type: str = "attachment",
        as_attachment: typing.Optional[bool] = None,
    ) -> None:
        if isinstance(path, IOBase):
            path.close()
            path = getattr(path, "name", None)

            if path is None:
                raise Exception("Not support this type")

        if as_attachment is not None and as_attachment is False:
            content_disposition_type = "inline"

        super().__init__(
            path,
            status or status_code,
            headers,
            content_type or media_type,
            background,
            filename,
            stat_result,
            method,
            content_disposition_type,
        )


class StreamingResponse(ResponseHeaderOperatorsMixin, StarletteStreamingResponse):
    pass


class HttpResponseNotAllowed(HttpResponse):
    def __init__(self, permitted_methods, status_code: int = 405, **kwargs) -> None:
        super().__init__(
            None, status_code, headers={"Allow": ", ".join(permitted_methods)}, **kwargs
        )


class HttpResponseForbidden(HttpResponse):
    def __init__(self, content=None, status_code: int = 403, **kwargs) -> None:
        super().__init__(content, status_code, **kwargs)


class JsonResponseForbidden(JsonResponse):
    def __init__(self, content=None, status_code: int = 403, **kwargs) -> None:
        super().__init__(content or {"error": "Forbidden"}, status_code, **kwargs)
