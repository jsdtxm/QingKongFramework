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
from starlette.background import BackgroundTask


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


class HttpResponse(Response):
    pass


class HttpResponseNotAllowed(HttpResponse):
    def __init__(self, permitted_methods, status_code: int = 405, **kwargs) -> None:
        super().__init__(
            None, status_code, headers={"Allow": ", ".join(permitted_methods)}, **kwargs
        )
