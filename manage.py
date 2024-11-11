import multiprocessing

import click

from libs.ascii_art import print_logo
from libs.commands import db
from libs.proxy import run_proxy
from libs.serve import serve_app, serve_apps


@click.group()
def cli():
    pass


@cli.command()
@click.argument("app", default="all", type=click.STRING)
@click.option("--host", default="127.0.0.1", type=click.STRING)
@click.option("--workers", default=1, type=click.INT)
@click.option("--reload", is_flag=True)
def serve(app, host, workers, reload):
    if app == "all":
        serve_apps(host, workers, reload)
    else:
        serve_app(app, host, workers, reload)


@cli.command()
@click.option("--host", default="127.0.0.1", type=click.STRING)
@click.option("--port", default=8000, type=click.INT)
def proxy(host, port):
    run_proxy(host, port)


@cli.command()
def migrate():
    db.migrate()


@cli.command()
def about():
    print_logo()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    cli()
