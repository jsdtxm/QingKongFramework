from collections.abc import Mapping
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Type, Union

from fastapi import params
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.routing import APIRoute, APIRouter
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute

from libs.views.class_based import ViewWrapper


class ApiPath:
    def __init__(
        self,
        path: str,
        endpoint: Union[Callable[..., Any], "NestedRouter", "ViewWrapper"],
        name: Optional[str] = None,
        response_model: Any = Default(None),
        status_code: Optional[int] = None,
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        response_model_include: Optional[IncEx] = None,
        response_model_exclude: Optional[IncEx] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: Union[Type[Response], DefaultPlaceholder] = Default(
            JSONResponse
        ),
        route_class_override: Optional[Type[APIRoute]] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
        generate_unique_id_function: Union[
            Callable[[APIRoute], str], DefaultPlaceholder
        ] = Default(generate_unique_id),
    ):
        self.path = path
        self.endpoint = endpoint
        self.name = name
        self.response_model = response_model

        self.methods = methods


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
        elif isinstance(url.endpoint, ViewWrapper):
            if not url.path.startswith("/"):
                url.path = "/" + url.path

            router = APIRouter()
            for method in url.endpoint.view_class.implemented_methods():
                router.add_api_route(
                    "/",
                    url.endpoint.view,
                    name=url.name,
                    methods=[
                        method,
                    ],
                    response_model=url.response_model
                )
            router_list.append(RouterWrapper(router, url.path))
        else:
            if not url.path.startswith("/"):
                url.path = "/" + url.path
            root.add_api_route(url.path, url.endpoint, name=url.name, response_model=url.response_model, methods=url.methods)

    router_list.append(RouterWrapper(root))

    return router_list
