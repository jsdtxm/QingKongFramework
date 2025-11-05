import inspect
import pickle
from functools import wraps
from typing import Any, Callable, Optional, Union

from fastapp.cache.states import caches


def cached(
    func: Optional[Callable] = None,
    /,
    *,  # 强制使用关键字参数
    key: Optional[str] = None,
    timeout: Optional[int] = 300,
    key_prefix: Optional[str] = None,
    alias: str = "default",
) -> Union[Callable, Callable[[Callable], Callable]]:
    """
    缓存装饰器，使用框架自带的缓存接口缓存函数结果，语法与functools.lru_cache兼容。

    支持两种使用方式:
    1. 直接装饰: @cached
    2. 带参数调用: @cached(timeout=600, alias="redis")

    Args:
        func: 要装饰的异步函数（直接调用时）
        key: 缓存键，如果不提供则自动生成
        timeout: 缓存过期时间（秒），默认300秒
        key_prefix: 缓存键前缀
        alias: 缓存后端别名，默认"default"

    Returns:
        装饰后的函数或装饰器
    """

    def decorator(func: Callable) -> Callable:
        # 确保函数是异步的
        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                f"The function {func.__name__} must be a coroutine function"
            )

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            cache = caches[alias]

            # 生成缓存键
            cache_key = key
            if cache_key is None:
                # 自动生成缓存键
                cache_key = f"{func.__module__}:{func.__name__}"
                # 添加参数到缓存键
                if args:
                    cache_key += f":{':'.join(str(arg) for arg in args)}"
                if kwargs:
                    cache_key += (
                        f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
                    )

            # 添加前缀
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"

            # 尝试从缓存获取
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                # 使用pickle反序列化
                return pickle.loads(cached_value)

            # 执行函数
            result = await func(*args, **kwargs)

            # 使用pickle序列化并缓存结果
            await cache.set(cache_key, pickle.dumps(result), timeout)

            return result

        return wrapper

    # 支持直接装饰函数或带参数调用
    if func is None:
        return decorator
    return decorator(func)
