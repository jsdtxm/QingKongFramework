import multiprocessing

import click
import uvloop

from core import db
from libs.ascii_art import print_logo
from libs.batch_run import batch_run
from libs.proxy import run_proxy


@click.group()
def cli():
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", type=click.STRING)
@click.option("--workers", default=1, type=click.INT)
@click.option("--reload", is_flag=True)
def serve(host, workers, reload):
    batch_run(host, workers, reload)


@cli.command()
@click.option("--host", default="127.0.0.1", type=click.STRING)
@click.option("--port", default=8000, type=click.INT)
def proxy(host, port):
    run_proxy(host, port)


@cli.command()
def migrate():
    uvloop.run(db.init())
    print("COMPLETE")


@cli.command()
def about():
    print_logo()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    cli()
