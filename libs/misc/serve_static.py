import logging
import os
from pathlib import Path

import aiohttp
import aiohttp.web
import click
import uvloop
from aiohttp.web_exceptions import HTTPNotFound

from libs.misc.aiohttp_utils import aiohttp_print_override

access_logger = logging.getLogger("qingkong.access")
error_logger = logging.getLogger("qingkong.error")


def index_handler_factory(root_dir: Path):
    async def index_handler(request):
        # 尝试找到index.html
        filename = "index.html"
        requested_path = (root_dir / filename).resolve()

        if requested_path.exists():
            return aiohttp.web.FileResponse(requested_path)
        else:
            # 如果没有找到index.html，则返回404响应
            raise aiohttp.web.HTTPNotFound(text="No index.html found")

    return index_handler


def serve_static_factory(root_dir: Path, try_files: str):
    async def serve_static(request):
        filename = request.match_info["filename"]
        if "../" in filename:
            raise aiohttp.web.HTTPForbidden(text="Invalid path")

        requested_path = (root_dir / filename).resolve()

        # Ensure the path is within the root directory
        if root_dir != requested_path.parent and root_dir not in requested_path.parents:
            raise aiohttp.web.HTTPForbidden()

        if requested_path.exists() and requested_path.is_file():
            return aiohttp.web.FileResponse(requested_path)

        if try_files:
            return aiohttp.web.FileResponse((root_dir / "index.html").resolve())

        raise HTTPNotFound(text="File not found")

    return serve_static


def run_static_server(
    host="127.0.0.1", port=8000, root_dir="./static", try_files="index.html"
):
    root_dir = Path(root_dir).resolve()

    if not root_dir.exists():
        error_logger.error(f"Static directory {root_dir} does not exist.")
        return

    app = aiohttp.web.Application()
    app.router.add_get("/", index_handler_factory(root_dir))
    app.router.add_get("/{filename:.*}", serve_static_factory(root_dir, try_files))

    error_logger.info(
        f"Static server running on {click.style(f'http://{host}:{port}', fg='bright_white')} (Press CTRL+C to quit)"
    )
    error_logger.info(f"Started server process [{click.style(os.getpid(), fg='blue')}]")
    error_logger.info("Waiting for application startup.")

    aiohttp.web.run_app(
        app,
        host=host,
        port=port,
        loop=uvloop.new_event_loop(),
        print=aiohttp_print_override,
    )
