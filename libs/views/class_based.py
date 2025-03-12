import logging
from functools import update_wrapper
from typing import Any, Dict, Optional, Self, Type, TypeVar

from fastapi.routing import APIRouter
from starlette.requests import Request

from libs.contrib.auth.typing import UserProtocol
from libs.contrib.auth.utils import OptionalCurrentUser
from libs.requests import DjangoStyleRequest
from libs.responses import HttpResponse, HttpResponseNotAllowed
from libs.utils.functional import classonlymethod
from libs.utils.strings import split_camel_case

logger = logging.getLogger("qingkong.request")

RequestType = TypeVar("RequestType", bound=DjangoStyleRequest)


def view_name_clear(cls_name: str) -> str:
    return " ".join(split_camel_case(cls_name.replace("View", "")))


class ViewWrapper:
    def __init__(self, view, view_class: Type["View"], initkwargs: Dict[str, Any]):
        self.view_method = view
        self.view_class = view_class
        self.initkwargs = initkwargs

    async def django_request_adapter(
        self, request: Request, user: Optional[UserProtocol]
    ):
        new_request = self.view_class.request_class(request, user=user)
        await self.view_class.post_request_process(new_request)
        return new_request

    def view(self, url_params=[]):
        extra_params_str = (
            ", ".join([f"{item[0]}: {item[1]}" for item in url_params])
            if url_params
            else ""
        )
        extra_params_send = ", ".join(
            [f"{match[0]}={match[0]}" for match in url_params]
        )
        function_definition = f"""def view_wrapper_factory(self):
    async def view_wrapper(
        request: Request, user: self.view_class.authentication_class, {extra_params_str}
    ):
        return await self.view_method(
            await self.django_request_adapter(request, user), {extra_params_send}
        )
    return view_wrapper"""

        local_env = {}
        exec(
            function_definition,
            {
                "Request": Request,
            },
            local_env,
        )

        return local_env["view_wrapper_factory"](self)

    def as_router(
        self, name=None, response_model=None, response_class=None, url_params=[]
    ):
        router = APIRouter()
        for method in self.view_class.implemented_methods():
            router.add_api_route(
                "/",
                self.get_typed_view(self.view(url_params), method),
                name=name,
                methods=[
                    method,
                ],
                response_model=response_model,
                response_class=response_class,
                include_in_schema=True if method != "options" else False,
            )

        return router

    def get_typed_view(self, view, method: str):
        view.__name__ = f"{view_name_clear(self.view_class.__name__)}_{method}"

        return view


class View:
    """
    Intentionally simple parent class for all views. Only implements
    dispatch-by-method and simple sanity checking.
    """

    wrapper_class = ViewWrapper

    authentication_class: Any = OptionalCurrentUser
    request_class = DjangoStyleRequest

    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
        "trace",
    ]

    def __init__(self, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        # Go through keyword arguments, and either save their values to our
        # instance, or raise an error.
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    async def post_request_process(self, request: RequestType):
        pass

    @classonlymethod  # type: ignore
    def as_view(cls, **initkwargs):
        """Main entry point for a request-response process."""
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError(
                    "The method name %s is not accepted as a keyword argument "
                    "to %s()." % (key, cls.__name__)
                )
            if not hasattr(cls, key):
                raise TypeError(
                    "%s() received an invalid keyword %r. as_view "
                    "only accepts arguments that are already "
                    "attributes of the class." % (cls.__name__, key)
                )

        def view(request: DjangoStyleRequest, *args, **kwargs):
            self: Self = cls(**initkwargs)  # type: ignore
            self.setup(request, *args, **kwargs)
            if not hasattr(self, "request"):
                raise AttributeError(
                    "%s instance has no 'request' attribute. Did you override "
                    "setup() and forget to call super()?" % cls.__name__  # type: ignore
                )
            return self.dispatch(request, *args, **kwargs)

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())

        return cls.wrapper_class(view, cls, initkwargs)

    def setup(self, request: DjangoStyleRequest, *args, **kwargs):
        """Initialize attributes shared by all view methods."""
        if hasattr(self, "get") and not hasattr(self, "head"):
            self.head = self.get
        self.request = request
        self.args = args
        self.kwargs = kwargs

    def dispatch(self, request: DjangoStyleRequest, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if request.method.lower() in self.http_method_names:
            handler = getattr(
                self, request.method.lower(), self.http_method_not_allowed
            )
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)

    async def http_method_not_allowed(
        self, request: DjangoStyleRequest, *args, **kwargs
    ):
        logger.warning(
            "Method Not Allowed (%s): %s",
            request.method,
            request.url,
            extra={"status_code": 405, "request": request},
        )
        return HttpResponseNotAllowed(self._allowed_methods())

    async def options(self, request: DjangoStyleRequest, *args, **kwargs):
        """Handle responding to requests for the OPTIONS HTTP verb."""
        response = HttpResponse()
        response.headers["Allow"] = ", ".join(self._allowed_methods())
        response.headers["Content-Length"] = "0"
        return response

    def _allowed_methods(self):
        return [m.upper() for m in self.http_method_names if hasattr(self, m)]

    @classmethod
    def implemented_methods(cls):
        return [m.lower() for m in cls.http_method_names if hasattr(cls, m)]
