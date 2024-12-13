import click

from libs.commands.utils import parse_dict
from libs.misc.ascii_art import print_logo
from libs.misc.gateway import run_gateway
from libs.misc.serve import serve_app, serve_apps


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
@click.option("--port", default=8000, type=click.INT)
@click.option("--upstream", callback=parse_dict, multiple=True)
@click.option("--default-upstream", default="127.0.0.1", type=click.STRING)
def gateway(host, port, upstream, default_upstream):
    print_logo()
    run_gateway(host, port, upstream, default_upstream)
