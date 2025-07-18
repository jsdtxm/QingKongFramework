import click

from fastapp.commands.utils import parse_dict
from fastapp.misc.ascii_art import print_logo
from fastapp.misc.gateway import run_gateway
from fastapp.misc.serve import serve_app, serve_app_aio, serve_apps
from fastapp.misc.serve_static import run_static_server


@click.argument("app", default="all", type=click.STRING)
@click.option("--host", default="127.0.0.1", type=click.STRING)
@click.option("--exclude", multiple=True, default=[])
@click.option("--workers", default=1, type=click.INT)
@click.option("--reload", is_flag=True)
def runserver(app, host, exclude, workers, reload):
    print_logo()
    if app == "all":
        serve_apps(host, workers, reload, exclude)
    else:
        serve_app(app, host, workers, reload)


@click.option("--host", default="127.0.0.1", type=click.STRING)
@click.option("--port", default=8080, type=click.INT)
@click.option("--workers", default=1, type=click.INT)
@click.option("--reload", is_flag=True)
def runserver_aio(host, port, workers, reload):
    print_logo()
    serve_app_aio(host, port, workers, reload)


@click.option("--host", default="127.0.0.1", type=click.STRING)
@click.option("--port", default=8000, type=click.INT)
@click.option("--upstream", callback=parse_dict, multiple=True)
@click.option("--default-upstream", default="127.0.0.1", type=click.STRING)
@click.option("--add-slashes", is_flag=True, type=click.BOOL)
@click.option("--fastapi-redirect", is_flag=True, type=click.BOOL)
@click.option("--redirect", is_flag=True, type=click.BOOL)
@click.option("--debug", is_flag=True, type=click.BOOL)
def gateway(host, port, upstream, default_upstream, add_slashes, fastapi_redirect, redirect, debug):
    print_logo()
    run_gateway(host, port, upstream, default_upstream, add_slashes, fastapi_redirect or redirect, debug)


@click.option("--host", default="127.0.0.1", type=click.STRING)
@click.option("--port", default=8080, type=click.INT)
@click.option("--root", default="./static", type=click.STRING)
@click.option("--api-prefix", default="/api", type=click.STRING)
@click.option("--api-target", default="http://127.0.0.1:8000", type=click.STRING)
def serve_static(host, port, root, api_prefix, api_target):
    print_logo()
    run_static_server(host, port, root_dir=root, api_prefix=api_prefix, api_target=api_target)
