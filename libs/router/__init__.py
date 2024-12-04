from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Callable, List, Optional, override

from fastapi.routing import APIRouter

from libs.utils.typing import copy_method_signature


class ApiPath:
    if TYPE_CHECKING:

        @override
        def __init__(
            self,
            path: str,
            endpoint: Any,
            **kwargs,
        ): ...

    @copy_method_signature(APIRouter.add_api_route)
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        name: Optional[str] = None,
        **kwargs,
    ):
        self.path = path
        self.endpoint = endpoint
        self.name = name
        self.kwargs = kwargs


path = ApiPath


class NestedRouter:
    def __init__(
        self,
        inner: APIRouter,
    ):
        self.inner = inner


include = NestedRouter


class RouterWrapper(Mapping):
    _FIELDS = ["router", "prefix"]

    def __init__(self, router: APIRouter, prefix: str = ""):
        self.router = router
        self.prefix = prefix

    def __len__(self):
        return len(self._FIELDS)

    def __getitem__(self, name):
        return vars(self)[name]

    def __iter__(self):
        return iter(self._FIELDS)


def router_convert(urlpatterns: List[ApiPath]):
    router_list = []

    root = APIRouter()
    for url in urlpatterns:
        if isinstance(url.endpoint, NestedRouter):
            router_list.append(RouterWrapper(url.endpoint.inner, url.path))
        else:
            if not url.path.startswith("/"):
                url.path = "/" + url.path
            root.add_api_route(url.path, url.endpoint, name=url.name, **url.kwargs)

    router_list.append(RouterWrapper(root))

    return router_list
