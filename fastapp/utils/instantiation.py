from typing import Optional


def return_none_when_error(func):
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            print(f"[ERROR]: {e}")
            result = None
        return result

    return wrapper


def func_instantiation(source: str, func_name: str, global_env: Optional[dict] = None):
    local_env = {}
    exec(
        source,
        global_env or {},
        local_env,
    )

    return return_none_when_error(local_env[func_name])
