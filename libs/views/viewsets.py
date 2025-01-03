from collections import namedtuple
from functools import update_wrapper
from inspect import getmembers
from typing import Iterable, List, Self, Tuple

from fastapi.routing import APIRouter
from starlette.requests import Request

from libs.utils.functional import classonlymethod
from libs.views import mixins
from libs.views.class_based import View, ViewWrapper
from libs.views.decorators import ActionMethodMapper

# from rest_framework.viewsets import GenericViewSet

REST_ACTION_METHOD_MAPPING = {
    "list": ["get"],
    "retrieve": ["get"],
    "create": ["post"],
    "update": ["put"],
    "destroy": ["delete"],
}

ViewSetRouteItem = namedtuple("RouteItem", ["action", "url", "methods"])


class GenericViewSetWrapper(ViewWrapper):
    def get_routers(self, viewset: "GenericViewSet") -> Iterable[ViewSetRouteItem]:
        routers = []

        for name, action in viewset.get_actions():
            methods = REST_ACTION_METHOD_MAPPING[name]
            detail = name in {"retrieve", "update", "destroy"}

            routers.append(ViewSetRouteItem(name, "/{id}" if detail else "/", methods))

        for name, action in viewset.get_extra_actions():
            detail = getattr(action, "detail", False)

            routers.append(
                ViewSetRouteItem(
                    name,
                    ("/{id}/" if detail else "/") + action.url_path,
                    action.methods,
                )
            )

        return routers

    def view(self, action: str):
        async def view_wrapper(request: Request):
            return await self.view_method(action, self.django_request_adapter(request))

        return view_wrapper

    def as_router(self, name=None, response_model=None, response_class=None):
        router = APIRouter()
        for route_item in self.get_routers(self.view_class):
            router.add_api_route(
                route_item.url,
                self.get_typed_view(self.view(route_item.action), route_item.action),
                name=name,
                methods=route_item.methods,
                response_model=response_model,
                response_class=response_class,
                include_in_schema=True,
            )

        return router


def _is_extra_action(attr):
    return hasattr(attr, "detail")


def _check_attr_name(name, func):
    assert func.__name__ == name, (
        "Expected function (`{func.__name__}`) to match its attribute name "
        "(`{name}`). If using a decorator, ensure the inner function is "
        "decorated with `functools.wraps`, or that `{func.__name__}.__name__` "
        "is otherwise set to `{name}`."
    ).format(func=func, name=name)
    return name, func


class GenericViewSet(View):
    action: str

    wrapper_class = GenericViewSetWrapper

    @classmethod
    def get_actions(cls):
        actions = []
        for name in REST_ACTION_METHOD_MAPPING:
            if method := getattr(cls, name, None):
                actions.append((name, method))
        return actions

    @classmethod
    def get_extra_actions(cls) -> List[Tuple[str, ActionMethodMapper]]:
        return [
            _check_attr_name(name, method)
            for name, method in getmembers(cls, _is_extra_action)
        ]

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

        def view(action: str, request: Request, *args, **kwargs):
            self: Self = cls(**initkwargs)  # type: ignore
            self.action = action
            self.setup(request, *args, **kwargs)
            if not hasattr(self, "request"):
                raise AttributeError(
                    "%s instance has no 'request' attribute. Did you override "
                    "setup() and forget to call super()?" % cls.__name__  # type: ignore
                )
            return self.dispatch(request, *args, **kwargs)

        # view.view_class = cls
        # view.view_initkwargs = initkwargs

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())

        return cls.wrapper_class(view, cls, initkwargs)

    def setup(self, request: Request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.kwargs = kwargs

    def dispatch(self, request: Request, *args, **kwargs):
        handler = getattr(self, self.action, self.http_method_not_allowed)

        return handler(request, *args, **kwargs)


class ReadOnlyModelViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """

    pass
