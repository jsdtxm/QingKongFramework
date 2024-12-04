import multiprocessing

from libs.commands import about, cli, migrate, runserver

cli.command()(runserver)
cli.command()(migrate)
cli.command()(about)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    cli()
