import logging

import aiohttp

access_logger = logging.getLogger("qingkong.access")
error_logger = logging.getLogger("qingkong.error")


def aiohttp_print_override(*args, **kwargs):
    error_logger.info("Application startup complete.")


async def log_middleware(app, handler):
    async def middleware_handler(request: aiohttp.web.Request):
        response: aiohttp.web.Response = await handler(request)
        access_logger.info(
            '%s - "%s %s HTTP/%s" %d',
            request.remote,
            request.method,
            request.path_qs,
            f"{request.version.major}.{request.version.minor}",
            response.status,
        )
        return response

    return middleware_handler


async def error_middleware(app, handler):
    async def middleware_handler(request: aiohttp.web.Request):
        try:
            return await handler(request)
        except aiohttp.web.HTTPException as ex:
            return aiohttp.web.json_response({"error": str(ex)}, status=ex.status)
        except aiohttp.client_exceptions.ClientConnectorError:
            return aiohttp.web.json_response(
                {
                    "error": "Bad Gateway",
                    "message": "Upstream server is currently unavailable.",
                },
                status=502,
            )
        except Exception as ex:
            return aiohttp.web.json_response(
                {"error": "Internal Server Error", "message": str(ex)}, status=500
            )

    return middleware_handler
