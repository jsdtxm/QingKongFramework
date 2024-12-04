import click
from libs.misc.create import create_app

@click.argument("app_name", type=click.STRING)
def startapp(app_name):
    create_app(app_name)
