from starlette.responses import FileResponse as FileResponse  # noqa
from starlette.responses import HTMLResponse as HTMLResponse  # noqa
from starlette.responses import JSONResponse as StarletteJSONResponse  # noqa
from starlette.responses import PlainTextResponse as PlainTextResponse  # noqa
from starlette.responses import RedirectResponse as RedirectResponse  # noqa
from starlette.responses import Response as Response  # noqa
from starlette.responses import StreamingResponse as StreamingResponse  # noqa
import json
import typing
from libs.utils.json import JSONEncoder


class JsonDumpsMixin:
    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            cls=JSONEncoder,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


class JSONResponse(JsonDumpsMixin, StarletteJSONResponse):
    pass


class JsonResponse(JsonDumpsMixin, StarletteJSONResponse):
    pass


class HttpResponse(Response):
    pass


class HttpResponseNotAllowed(HttpResponse):
    def __init__(self, permitted_methods, status_code: int = 405, **kwargs) -> None:
        super().__init__(
            None, status_code, headers={"Allow": ", ".join(permitted_methods)}, **kwargs
        )
