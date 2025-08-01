import re
from collections.abc import Mapping
from enum import Enum
from itertools import chain
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Type, Union

from fastapi import params
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.routing import APIRoute as FastapiAPIRoute
from fastapi.routing import APIRouter as FastapiAPIRouter
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id
from starlette.responses import Response
from starlette.routing import BaseRoute

from fastapp.responses import JSONResponse
from fastapp.router.utils import CURLY_BRACKET_WITH_TYPE_REGEX
from fastapp.utils.strings import BRACE_REGEX, convert_url_format, extract_type_and_name
from fastapp.views.class_based import ViewWrapper


class APIRoute(FastapiAPIRoute):
    def __init__(
        self,
        *args,
        response_class=JSONResponse,
        **kwargs,
    ) -> None:
        return super().__init__(*args, response_class=response_class, **kwargs)


class APIRouter(FastapiAPIRouter):
    def __init__(
        self,
        *,
        route_class=APIRoute,
        **kwargs,
    ) -> None:
        return super().__init__(route_class=route_class, **kwargs)


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

        self.dependencies = dependencies

        self.methods = methods

        self.response_class = response_class


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
            if url.path and not url.path.startswith("/"):
                url.path = "/" + url.path

            router_list.append(RouterWrapper(url.endpoint.inner, url.path))
        elif isinstance(url.endpoint, ViewWrapper):
            if not url.path.startswith("/"):
                url.path = "/" + url.path
            if url.path.endswith("/"):
                url.path = url.path[:-1]

            if url.endpoint.__class__ is ViewWrapper:
                # url 参数提取，排除viewset

                url.path = url.path.replace(" ", "")

                url_curly_params = []
                url_angle_params = []

                if "<" in url.path:
                    url_angle_params = extract_type_and_name(url.path)

                if "{" in url.path:
                    url_curly_params = [
                        (x, "int") for x in re.findall(BRACE_REGEX, url.path)
                    ]

                    if not url_curly_params:
                        url_curly_params = [
                            x
                            for x in re.findall(CURLY_BRACKET_WITH_TYPE_REGEX, url.path)
                        ]

                        if url_curly_params:
                            url.path = re.sub(
                                CURLY_BRACKET_WITH_TYPE_REGEX, r"{\1}", url.path
                            )

                if url_angle_params:
                    url.path = convert_url_format(url.path)

                url_params = list(chain(url_curly_params, url_angle_params))

                if url_params:
                    router = url.endpoint.as_router(
                        url.name,
                        url.response_model,
                        url.response_class,
                        url_params=url_params,
                    )

                    router_list.append(RouterWrapper(router, url.path))
                    continue

            router = url.endpoint.as_router(
                url.name, url.response_model, url.response_class
            )

            router_list.append(RouterWrapper(router, url.path))
        else:
            if not url.path.startswith("/"):
                url.path = "/" + url.path
            if url.path.endswith("/"):
                url.path = url.path[:-1]

            root.add_api_route(
                url.path,
                url.endpoint,
                name=url.name,
                methods=url.methods,
                response_model=url.response_model,
                response_class=url.response_class,
            )

    router_list.append(RouterWrapper(root))

    return router_list
