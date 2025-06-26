import inspect
import pickle
from functools import lru_cache
from typing import Awaitable, Callable, Dict, ParamSpec, Protocol, TypeVar, cast

import aiohttp
from starlette.responses import Response

from fastapp.utils.fs import read_port_from_json
from fastapp.utils.module_loading import cached_import_module

P = ParamSpec("P")
R = TypeVar("R")


class CrossServiceFunc(Protocol[P, R]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    call: Callable[P, Awaitable[R]]


@lru_cache
def find_service_app(package: str) -> str:
    package_parts = package.split(".")

    app = None
    for i in range(len(package_parts), 1, -1):
        module_package = ".".join(package_parts[:i])
        try:
            cached_import_module(module_package + ".apps")
        except ModuleNotFoundError:
            continue
        app = module_package

    if app is None:
        raise Exception(f"Cannot find service app for package {package}")

    return app


@lru_cache
def get_app_base_url(app: str) -> str:
    base_url = read_port_from_json(app)
    return f"{base_url['address']}:{base_url['port']}"


async def call_remote_api(base_url, end_point, all_kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://{base_url}/_internal/{end_point}", json=all_kwargs) as response:
            content = await response.read()
            resp_object = pickle.loads(content)
            if isinstance(resp_object, Exception):
                raise resp_object

            return resp_object


def cross_service(func: Callable[P, R]) -> CrossServiceFunc[P, R]:
    signature = inspect.signature(func)

    module = inspect.getmodule(func)
    if module is None:
        raise Exception(f"Cannot find module for function {func}")

    app = find_service_app(module.__package__)
    base_url = get_app_base_url(app)

    def call(*args: P.args, **kwargs: P.kwargs) -> R:
        # 绑定参数
        bound_args = signature.bind(*args, **kwargs)
        # 应用默认值
        bound_args.apply_defaults()

        # 转换为完整 kwargs 字典
        all_kwargs = dict(bound_args.arguments)

        return call_remote_api(base_url, func.__name__, all_kwargs)

    async def use_post_body(kwargs: Dict):
        try:
            result = await func(**kwargs)
        except Exception as e:
            return Response(content=pickle.dumps(e), media_type="application/octet-stream", status_code=500)

        return Response(content=pickle.dumps(result), media_type="application/octet-stream")

    func._cross_service = True
    func.call = call  # type: ignore[attr-defined]
    func.wrapped_view = use_post_body  # type: ignore[attr-defined]

    return cast(CrossServiceFunc[P, R], func)
