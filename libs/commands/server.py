import click

from libs.misc.proxy import run_proxy
from libs.misc.serve import serve_app, serve_apps


@click.argument("app", default="all", type=click.STRING)
@click.option("--host", default="127.0.0.1", type=click.STRING)
@click.option("--workers", default=1, type=click.INT)
@click.option("--reload", is_flag=True)
def runserver(app, host, workers, reload):
    if app == "all":
        serve_apps(host, workers, reload)
    else:
        serve_app(app, host, workers, reload)


@click.option("--host", default="127.0.0.1", type=click.STRING)
@click.option("--port", default=8000, type=click.INT)
@click.option("--upstream", default="127.0.0.1", type=click.STRING)
def proxy(host, port, upstream):
    run_proxy(host, port, upstream)
